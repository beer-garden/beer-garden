import logging
from typing import List, Optional, cast
from uuid import uuid4

import yaml
from box import Box
from brewtils.schemas import RoleAssignmentSchema as BrewtilsRoleAssignmentSchema
from marshmallow import Schema, ValidationError, fields, post_load, validates
from tornado.httputil import HTTPHeaders, HTTPServerRequest
from yaml.parser import ParserError

from beer_garden import config
from beer_garden.api.http.authentication.login_handlers.base import BaseLoginHandler
from beer_garden.db.mongo.models import Role, RoleAssignment, User
from beer_garden.errors import ConfigurationError

logger = logging.getLogger(__name__)


class SimpleRoleAssignmentSchema(BrewtilsRoleAssignmentSchema):
    """Schema for RoleAssignment that allows specifying a role name rather than a
    Role object"""

    role_name = fields.Str(required=True)


class RoleAssignmentSchema(SimpleRoleAssignmentSchema):
    """Schema for deserializing role assignments from the group mapping config"""

    _role = None

    @validates("role_name")
    def validate_role_name(self, value):
        try:
            # Stash the Role so that we don't have to re-query the db for it later
            self._role = Role.objects.get(name=value)
        except Role.DoesNotExist:
            raise ValidationError(f"Invalid role_name {value}. No such role found.")

    @post_load
    def load_obj(self, item, **kwargs):
        item["role"] = self._role
        del item["role_name"]

        return RoleAssignment(**item)


class GroupMappingSchema(Schema):
    """Schema for validating the group mapping config"""

    group = fields.Str(required=True)
    role_assignments = fields.List(
        fields.Nested(SimpleRoleAssignmentSchema), required=True
    )


class TrustedHeaderLoginHandler(BaseLoginHandler):
    """Handler for certificate based authentication"""

    def __init__(self):
        handler_config = cast(
            Box, config.get("auth.authentication_handlers.trusted_header")
        )
        self.username_header = handler_config.get("username_header")
        self.user_groups_header = handler_config.get("user_groups_header")
        self.create_users = handler_config.get("create_users")
        self.group_definition_file = cast(str, config.get("auth.group_definition_file"))
        self.group_mapping = {}

        if self.group_definition_file:
            try:
                self.group_mapping = self._load_group_mapping(
                    self.group_definition_file
                )
            except ConfigurationError as exc:
                logger.error("Error loading group definitions: %s", exc)
        else:
            logger.error(
                "No group_definition_file defined. Users will not be assigned to any "
                "groups. To fix this, set the 'auth.group_definition_file' "
                "configuration parameter and restart beer garden."
            )

    def get_user(self, request: HTTPServerRequest) -> Optional[User]:
        """Gets the User based on certificates supplied with in the request body

        Args:
            request: tornado HTTPServerRequest object

        Returns:
            User: The User object for the user specified by the certificates
            None: If no User was found
        """
        authenticated_user: Optional[User] = None

        if request.headers and self.group_mapping:
            username = request.headers.get(self.username_header)
            groups = self._groups_from_headers(request.headers)

            if username and groups:
                try:
                    authenticated_user = User.objects.get(username=username)
                except User.DoesNotExist:
                    if self.create_users:
                        authenticated_user = User(username=username)

                        # TODO: Really we should just have an option on User to disable
                        # password logins. For now, just set a random-ish value.
                        authenticated_user.set_password(str(uuid4()))

                if authenticated_user:
                    authenticated_user.role_assignments = (
                        self._role_assignments_from_groups(groups)
                    )

                    authenticated_user.save()

        return authenticated_user

    def _groups_from_headers(self, headers: HTTPHeaders) -> List[str]:
        """Parse the header containing the user's groups and return them as a list"""
        return [
            group.strip()
            for group in headers.get(self.user_groups_header, "").split(",")
        ]

    def _role_assignments_from_groups(self, groups: List[str]):
        """Generate a list of RoleAssignments using the supplied groups and the
        configured group to role assignment mapping
        """
        role_assignments = []
        schema = RoleAssignmentSchema(strict=True)

        for group in groups:
            group_role_assignments = self.group_mapping.get(group)

            if group_role_assignments is None:
                continue

            for item in group_role_assignments:
                try:
                    role_assignment = schema.load(item).data
                    role_assignments.append(role_assignment)
                except ValidationError as exc:
                    logger.error(
                        f"Role assignment definition for {group} is malformed. One or "
                        "more role assignments will be not be mapped for this group. "
                        f"Failed to load with error: {exc}"
                    )
                    continue

        return role_assignments

    def _group_mapping_by_group_name(self, raw_group_mapping: List[dict]) -> dict:
        """Organize the group mapping by group name for ease of use"""
        group_mapping = {}

        for mapping in raw_group_mapping:
            group_mapping[mapping["group"]] = mapping["role_assignments"]

        return group_mapping

    def _load_group_mapping(self, group_definition_file: str) -> dict:
        """Read the supplied mapping file and return group mapping"""
        try:
            with open(group_definition_file, "r") as filestream:
                unvalidated_group_mapping = yaml.safe_load(filestream)
        except FileNotFoundError:
            raise ConfigurationError(
                f"Group mapping configuration file {group_definition_file} not found."
            )
        except ParserError as exc:
            raise ConfigurationError(
                f"Group mapping configuration file {group_definition_file} is "
                f"malformed. Failed to load with error: {exc}"
            )

        try:
            schema = GroupMappingSchema(strict=True, many=True)
            raw_group_mapping = schema.load(unvalidated_group_mapping).data
        except ValidationError as exc:
            raise ConfigurationError(
                f"Group mapping file is malformed. Validation error was: {exc}"
            )

        return self._group_mapping_by_group_name(raw_group_mapping)
