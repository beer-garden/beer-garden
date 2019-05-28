import logging

from tornado.gen import coroutine
from tornado.locks import Lock

from bg_utils.mongo.models import System, Instance
from bg_utils.mongo.parser import MongoParser
from brew_view import thrift_context
from brew_view.authorization import authenticated, Permissions
from brew_view.base_handler import BaseHandler
from brewtils.errors import ModelValidationError
from brewtils.models import Events
from brewtils.schemas import SystemSchema


class SystemAPI(BaseHandler):

    parser = MongoParser()
    logger = logging.getLogger(__name__)

    @authenticated(permissions=[Permissions.SYSTEM_READ])
    def get(self, system_id):
        """
        ---
        summary: Retrieve a specific System
        parameters:
          - name: system_id
            in: path
            required: true
            description: The ID of the System
            type: string
          - name: include_commands
            in: query
            required: false
            description: Include the System's commands in the response
            type: boolean
            default: true
        responses:
          200:
            description: System with the given ID
            schema:
              $ref: '#/definitions/System'
          404:
            $ref: '#/definitions/404Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Systems
        """
        self.logger.debug("Getting System: %s", system_id)

        include_commands = (
            self.get_query_argument("include_commands", default="true").lower()
            != "false"
        )
        self.write(
            self.parser.serialize_system(
                System.objects.get(id=system_id),
                to_string=False,
                include_commands=include_commands,
            )
        )

    @coroutine
    @authenticated(permissions=[Permissions.SYSTEM_DELETE])
    def delete(self, system_id):
        """
        Will give Bartender a chance to remove instances of this system from the
        registry but will always delete the system regardless of whether the Bartender
        operation succeeds.
        ---
        summary: Delete a specific System
        description: Will remove instances of local plugins from the registry, clear
            and remove message queues, and remove the system from the database.
        parameters:
          - name: system_id
            in: path
            required: true
            description: The ID of the System
            type: string
        responses:
          204:
            description: System has been successfully deleted
          404:
            $ref: '#/definitions/404Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Systems
        """
        self.request.event.name = Events.SYSTEM_REMOVED.name
        self.request.event_extras = {"system": System.objects.get(id=system_id)}

        with thrift_context() as client:
            yield client.removeSystem(str(system_id))

        self.set_status(204)

    @coroutine
    @authenticated(permissions=[Permissions.SYSTEM_UPDATE])
    def patch(self, system_id):
        """
        ---
        summary: Partially update a System
        description: |
          The body of the request needs to contain a set of instructions detailing the
          updates to apply.
          Currently supported operations are below:
          ```JSON
          {
            "operations": [
              { "operation": "replace", "path": "/commands", "value": "" },
              { "operation": "replace", "path": "/description", "value": "new description"},
              { "operation": "replace", "path": "/display_name", "value": "new display name"},
              { "operation": "replace", "path": "/icon_name", "value": "new icon name"},
              { "operation": "update", "path": "/metadata", "value": {"foo": "bar"}}
            ]
          }
          ```
          Where `value` is a list of new Commands.
        parameters:
          - name: system_id
            in: path
            required: true
            description: The ID of the System
            type: string
          - name: patch
            in: body
            required: true
            description: Instructions for how to update the System
            schema:
              $ref: '#/definitions/Patch'
        responses:
          200:
            description: System with the given ID
            schema:
              $ref: '#/definitions/System'
          400:
            $ref: '#/definitions/400Error'
          404:
            $ref: '#/definitions/404Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Systems
        """
        self.request.event.name = Events.SYSTEM_UPDATED.name

        system = System.objects.get(id=system_id)
        operations = self.parser.parse_patch(
            self.request.decoded_body, many=True, from_string=True
        )

        for op in operations:
            if op.operation == "replace":
                if op.path == "/commands":
                    new_commands = self.parser.parse_command(op.value, many=True)

                    if (
                        system.commands
                        and "dev" not in system.version
                        and system.has_different_commands(new_commands)
                    ):
                        raise ModelValidationError(
                            "System %s-%s already exists with different commands"
                            % (system.name, system.version)
                        )

                    system.upsert_commands(new_commands)
                elif op.path in ["/description", "/icon_name", "/display_name"]:
                    if op.value is None:
                        # If we set an attribute to None, mongoengine marks that
                        # attribute for deletion, so we don't do that.
                        value = ""
                    else:
                        value = op.value
                    attr = op.path.strip("/")
                    self.logger.debug("Updating system %s" % attr)
                    self.logger.debug("Old: %s" % getattr(system, attr))
                    setattr(system, attr, value)
                    self.logger.debug("Updated: %s" % getattr(system, attr))
                    system.save()
                else:
                    error_msg = "Unsupported path '%s'" % op.path
                    self.logger.warning(error_msg)
                    raise ModelValidationError("value", error_msg)
            elif op.operation == "update":
                if op.path == "/metadata":
                    self.logger.debug("Updating system metadata")
                    self.logger.debug("Old: %s" % system.metadata)
                    system.metadata.update(op.value)
                    self.logger.debug("Updated: %s" % system.metadata)
                    system.save()
                else:
                    error_msg = "Unsupported path for update '%s'" % op.path
                    self.logger.warning(error_msg)
                    raise ModelValidationError("path", error_msg)
            elif op.operation == "reload":
                with thrift_context() as client:
                    yield client.reloadSystem(system_id)
            else:
                error_msg = "Unsupported operation '%s'" % op.operation
                self.logger.warning(error_msg)
                raise ModelValidationError("value", error_msg)

        system.reload()

        self.request.event_extras = {"system": system, "patch": operations}

        self.write(self.parser.serialize_system(system, to_string=False))


class SystemListAPI(BaseHandler):

    parser = MongoParser()
    logger = logging.getLogger(__name__)

    REQUEST_FIELDS = set(SystemSchema.get_attribute_names())

    # Need to ensure that Systems are updated atomically
    system_lock = Lock()

    @authenticated(permissions=[Permissions.SYSTEM_READ])
    def get(self):
        """
        ---
        summary: Retrieve all Systems
        description: |
          This endpoint allows for querying Systems.

          There are several parameters that control which fields are returned
          and what information is available. Things to be aware of:

          * The `include_commands` parameter is __deprecated__. Don't use it.
            Use `exclude_fields=commands` instead.

          * It's possible to specify `include_fields` _and_ `exclude_fields`.
            This doesn't make a lot of sense, but you can do it. If the same
            field is in both `exclude_fields` takes priority (the field will
            NOT be included in the response).

          Systems matching specific criteria can be filtered using additional
          query parameters. This is a very basic capability:

          * ?name=foo&version=1.0.0
            This will return the system named 'foo' with version '1.0.0'
          * ?name=foo&name=bar
            This will not do what you expect: only return the system named
            'bar' will be returned.
        parameters:
          - name: include_fields
            in: query
            required: false
            description: Specify fields to include in the response. All other
              fields will be excluded.
            type: array
            collectionFormat: csv
            items:
              type: string
          - name: exclude_fields
            in: query
            required: false
            description: Specify fields to exclude from the response
            type: array
            collectionFormat: csv
            items:
              type: string
          - name: dereference_nested
            in: query
            required: false
            description: Commands and instances will be an object id
            type: boolean
            default: true
          - name: include_commands
            in: query
            required: false
            description: __DEPRECATED__ Include commands in the response.
              Use `exclude_fields=commands` instead.
            type: boolean
            default: true
        responses:
          200:
            description: All Systems
            schema:
              type: array
              items:
                $ref: '#/definitions/System'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Systems
        """
        query_set = System.objects.order_by(
            self.request.headers.get("order_by", "name")
        )
        serialize_params = {"to_string": True, "many": True}

        include_fields = self.get_query_argument("include_fields", None)
        exclude_fields = self.get_query_argument("exclude_fields", None)
        dereference_nested = self.get_query_argument("dereference_nested", None)
        include_commands = self.get_query_argument("include_commands", None)

        if include_fields:
            include_fields = set(include_fields.split(",")) & self.REQUEST_FIELDS
            query_set = query_set.only(*include_fields)
            serialize_params["only"] = include_fields

        if exclude_fields:
            exclude_fields = set(exclude_fields.split(",")) & self.REQUEST_FIELDS
            query_set = query_set.exclude(*exclude_fields)
            serialize_params["exclude"] = exclude_fields

        if include_commands and include_commands.lower() == "false":
            query_set = query_set.exclude("commands")

            if "exclude" not in serialize_params:
                serialize_params["exclude"] = set()
            serialize_params["exclude"].add("commands")

        if dereference_nested and dereference_nested.lower() == "false":
            query_set = query_set.no_dereference()

        # TODO - Handle multiple query arguments with the same key
        # for example: (?name=foo&name=bar) ... what should that mean?
        filter_params = {}

        # Need to use self.request.query_arguments to get all the query args
        for key in self.request.query_arguments:
            if key in self.REQUEST_FIELDS:
                # Now use get_query_argument to get the decoded value
                filter_params[key] = self.get_query_argument(key)

        result_set = query_set.filter(**filter_params)

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(self.parser.serialize_system(result_set, **serialize_params))

    @coroutine
    @authenticated(permissions=[Permissions.SYSTEM_CREATE])
    def post(self):
        """
        ---
        summary: Create a new System or update an existing System
        description: |
            If the System does not exist it will be created. If the System
            already exists it will be updated (assuming it passes validation).
        parameters:
          - name: system
            in: body
            description: The System definition to create / update
            schema:
              $ref: '#/definitions/System'
        responses:
          200:
            description: An existing System has been updated
            schema:
              $ref: '#/definitions/System'
          201:
            description: A new System has been created
            schema:
              $ref: '#/definitions/System'
          400:
            $ref: '#/definitions/400Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Systems
        """
        self.request.event.name = Events.SYSTEM_CREATED.name

        system_model = self.parser.parse_system(
            self.request.decoded_body, from_string=True
        )

        with (yield self.system_lock.acquire()):
            # See if we already have a system with this name + version
            existing_system = System.find_unique(
                system_model.name, system_model.version
            )

            if not existing_system:
                self.logger.debug("Creating a new system: %s" % system_model.name)
                saved_system, status_code = self._create_new_system(system_model)
            else:
                self.logger.debug(
                    "System %s already exists. Updating it." % system_model.name
                )
                self.request.event.name = Events.SYSTEM_UPDATED.name
                saved_system, status_code = self._update_existing_system(
                    existing_system, system_model
                )

            saved_system.deep_save()

        self.request.event_extras = {"system": saved_system}

        self.set_status(status_code)
        self.write(
            self.parser.serialize_system(
                saved_system, to_string=False, include_commands=True
            )
        )

    @staticmethod
    def _create_new_system(system_model):
        new_system = system_model

        # Assign a default 'main' instance if there aren't any instances and there can
        # only be one
        if not new_system.instances or len(new_system.instances) == 0:
            if new_system.max_instances is None or new_system.max_instances == 1:
                new_system.instances = [Instance(name="default")]
                new_system.max_instances = 1
            else:
                raise ModelValidationError(
                    "Could not create system %s-%s: Systems with "
                    "max_instances > 1 must also define their instances"
                    % (system_model.name, system_model.version)
                )
        else:
            if not new_system.max_instances:
                new_system.max_instances = len(new_system.instances)

        return new_system, 201

    @staticmethod
    def _update_existing_system(existing_system, system_model):
        # Raise an exception if commands already exist for this system and they differ
        # from what's already in the database in a significant way
        if (
            existing_system.commands
            and "dev" not in existing_system.version
            and existing_system.has_different_commands(system_model.commands)
        ):
            raise ModelValidationError(
                "System %s-%s already exists with different commands"
                % (system_model.name, system_model.version)
            )
        else:
            existing_system.upsert_commands(system_model.commands)

        # Update instances
        if not system_model.instances or len(system_model.instances) == 0:
            system_model.instances = [Instance(name="default")]

        for attr in ["description", "icon_name", "display_name"]:
            value = getattr(system_model, attr)

            # If we set an attribute on the model as None, mongoengine marks the
            # attribute for deletion. We want to prevent this, so we set it to an emtpy
            # string.
            if value is None:
                setattr(existing_system, attr, "")
            else:
                setattr(existing_system, attr, value)

        # Update metadata
        new_metadata = system_model.metadata or {}
        existing_system.metadata.update(new_metadata)

        old_instances = [
            inst
            for inst in existing_system.instances
            if system_model.has_instance(inst.name)
        ]
        new_instances = [
            inst
            for inst in system_model.instances
            if not existing_system.has_instance(inst.name)
        ]
        existing_system.instances = old_instances + new_instances

        return existing_system, 200
