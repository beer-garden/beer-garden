# -*- coding: utf-8 -*-
import datetime

import pytest
from mongoengine import connect
from mongomock.gridfs import enable_gridfs_integration

from beer_garden.authorization import (
    permissions_for_user,
    user_has_permission_for_object,
    user_permitted_objects,
)
from beer_garden.db.mongo.api import to_brewtils
from beer_garden.db.mongo.models import (
    Garden,
    IntervalTrigger,
    Job,
    Request,
    RequestTemplate,
    Role,
    RoleAssignment,
    System,
    User,
)

enable_gridfs_integration()


@pytest.fixture(autouse=True)
def drop():
    Garden.drop_collection()
    Role.drop_collection()
    System.drop_collection()
    User.drop_collection()


@pytest.fixture()
def role_for_garden_scope():
    role = Role(
        name="gardenreader",
        permissions=["garden:read", "system:read", "job:read", "request:read"],
    ).save()

    yield role
    role.delete()


@pytest.fixture()
def role_for_system_scope():
    role = Role(
        name="requestcreator", permissions=["request:create", "request:read"]
    ).save()

    yield role
    role.delete()


@pytest.fixture()
def role_for_global_scope():
    role = Role(name="gardencreator", permissions=["garden:create"]).save()

    yield role
    role.delete()


@pytest.fixture()
def role_assignment_for_garden_scope(role_for_garden_scope):
    yield RoleAssignment(
        domain={"scope": "Garden", "identifiers": {"name": "testgarden"}},
        role=role_for_garden_scope,
    )


@pytest.fixture()
def role_assignment_for_system_scope(role_for_system_scope):
    yield RoleAssignment(
        domain={
            "scope": "System",
            "identifiers": {"name": "testsystem1", "namespace": "testgarden"},
        },
        role=role_for_system_scope,
    )


@pytest.fixture()
def role_assignment_for_global_scope(role_for_global_scope):
    yield RoleAssignment(
        domain={
            "scope": "Global",
        },
        role=role_for_global_scope,
    )


@pytest.fixture
def user_with_role_assignments(
    role_assignment_for_garden_scope,
    role_assignment_for_system_scope,
    role_assignment_for_global_scope,
):
    user = User(
        username="testuser",
        role_assignments=[
            role_assignment_for_garden_scope,
            role_assignment_for_system_scope,
            role_assignment_for_global_scope,
        ],
    ).save()

    yield user
    user.delete()


@pytest.fixture
def test_garden(role_assignment_for_garden_scope):
    garden = Garden(**role_assignment_for_garden_scope.domain.identifiers).save()

    yield garden
    garden.delete()


@pytest.fixture
def test_system_1_0_0(role_assignment_for_system_scope):
    system = System(
        version="1.0.0", **role_assignment_for_system_scope.domain.identifiers
    ).save()

    yield system
    system.delete()


@pytest.fixture
def test_system_2_0_0(role_assignment_for_system_scope):
    system = System(
        version="2.0.0", **role_assignment_for_system_scope.domain.identifiers
    ).save()

    yield system
    system.delete()


@pytest.fixture
def test_request_template(test_system_1_0_0):
    yield RequestTemplate(
        system=test_system_1_0_0.name,
        system_version=test_system_1_0_0.version,
        namespace=test_system_1_0_0.namespace,
        instance_name="test_instance",
        command="test_command",
    )


@pytest.fixture
def test_job(test_request_template):
    job = Job(
        name="testjob",
        request_template=test_request_template,
        trigger_type="interval",
        trigger=IntervalTrigger(),
    ).save()

    yield job
    job.delete()


@pytest.fixture
def test_request(test_request_template):
    request = Request(
        system=test_request_template.system,
        system_version=test_request_template.system_version,
        namespace=test_request_template.namespace,
        instance_name=test_request_template.instance_name,
        command=test_request_template.command,
        updated_at=datetime.datetime.utcnow,
    )
    request.save()

    yield request
    request.delete()


class TestAuth:
    @classmethod
    def setup_class(cls):
        connect("beer_garden", host="mongomock://localhost")

    def test_permissions_for_user_generates_expected_output(
        self,
        role_assignment_for_garden_scope,
        role_assignment_for_system_scope,
        role_assignment_for_global_scope,
        test_garden,
        test_system_1_0_0,
        test_system_2_0_0,
        user_with_role_assignments,
    ):
        """permissions_for_user should generate a dictionary accurately representing a
        User's permissions based on their role_assignments
        """
        user_permissions = permissions_for_user(user_with_role_assignments)
        domain_permissions = user_permissions["domain_permissions"]
        global_permissions = user_permissions["global_permissions"]

        for permission in role_assignment_for_garden_scope.role.permissions:
            assert permission in domain_permissions.keys()
            assert str(test_garden.id) in domain_permissions[permission]["garden_ids"]

        for permission in role_assignment_for_system_scope.role.permissions:
            assert permission in domain_permissions.keys()
            assert (
                str(test_system_1_0_0.id)
                in domain_permissions[permission]["system_ids"]
            )
            assert (
                str(test_system_2_0_0.id)
                in domain_permissions[permission]["system_ids"]
            )

        for permission in role_assignment_for_global_scope.role.permissions:
            assert permission in global_permissions

    def test_permissions_for_user_skips_nonexistent_objects(
        self,
        user_with_role_assignments,
    ):
        """permissions_for_user should skip role_assignments that correspond to no
        existing object and continue on without error
        """
        # Here we call permissions_for_user without using any of the fixtures
        # that generate Garden or System objects
        user_permissions = permissions_for_user(user_with_role_assignments)
        domain_permissions = user_permissions["domain_permissions"]

        for role_assignment in user_with_role_assignments.role_assignments:
            if role_assignment.domain.scope == "Global":
                continue

            for permission in role_assignment.role.permissions:
                assert len(domain_permissions[permission]["garden_ids"]) == 0
                assert len(domain_permissions[permission]["system_ids"]) == 0

    def test_user_has_permission_for_object_returns_true_when_permitted(
        self, test_garden, test_system_1_0_0, user_with_role_assignments
    ):
        """user_has_permission_for_object should return true for a permission and object
        for which they have a corresponding role_assignment
        """
        assert user_has_permission_for_object(
            user_with_role_assignments, "garden:read", test_garden
        )

        assert user_has_permission_for_object(
            user_with_role_assignments, "request:read", test_system_1_0_0
        )

    def test_user_has_permission_for_object_returns_true_when_permitted_via_global(
        self, test_garden, test_system_1_0_0, user_with_role_assignments
    ):
        """user_has_permission_for_object should return true for a permission and object
        for which they have a corresponding role_assignment for the "Global" scope
        """
        assert user_has_permission_for_object(
            user_with_role_assignments, "garden:create", test_garden
        )

    def test_user_has_permission_for_object_when_lacking_specified_permission(
        self,
        test_garden,
        test_system_1_0_0,
        user_with_role_assignments,
    ):
        """user_has_permission_for_object should return false for a permission and
        object for which they have no role_assignment granting the specified permission
        """
        assert not user_has_permission_for_object(
            user_with_role_assignments, "unassigned_permission", test_garden
        )

        assert not user_has_permission_for_object(
            user_with_role_assignments, "unassigned_permission", test_system_1_0_0
        )

    def test_user_has_permission_for_object_when_having_no_permissions(
        self,
        test_garden,
        test_system_1_0_0,
        user_with_role_assignments,
    ):
        """user_has_permission_for_object should return false for a permission and
        object for which they have no role_assignment granting any permission to the
        object, not just the specified one
        """
        user_with_role_assignments.role_assignments = []
        user_with_role_assignments.clear_permissions_cache()

        assert not user_has_permission_for_object(
            user_with_role_assignments, "request:read", test_system_1_0_0
        )

    def test_user_has_permission_for_object_job_through_garden(
        self,
        role_assignment_for_garden_scope,
        test_garden,
        test_job,
        user_with_role_assignments,
    ):
        """user_has_permission_for_object returns true for a System in which the
        user has Garden level access for the required permission
        """
        # Set the user's role assignments to be just the Garden scoped one (i.e. no
        # System scoped role assignments)
        user_with_role_assignments.role_assignments = [role_assignment_for_garden_scope]
        user_with_role_assignments.clear_permissions_cache()

        assert user_has_permission_for_object(
            user_with_role_assignments, "job:read", test_job
        )

    def test_user_has_permission_for_object_request_through_system(
        self,
        role_assignment_for_system_scope,
        test_request,
        test_system_1_0_0,
        user_with_role_assignments,
    ):
        """user_has_permission_for_object returns true for a System in which the
        user has Garden level access for the required permission
        """
        # Set the user's role assignments to be just the System scoped one
        user_with_role_assignments.role_assignments = [role_assignment_for_system_scope]
        user_with_role_assignments.clear_permissions_cache()

        assert user_has_permission_for_object(
            user_with_role_assignments, "request:create", test_request
        )

    def test_user_has_permission_for_object_system_through_garden(
        self,
        role_assignment_for_garden_scope,
        test_garden,
        test_system_1_0_0,
        user_with_role_assignments,
    ):
        """user_has_permission_for_object returns true for a System in which the
        user has Garden level access for the required permission
        """
        # Set the user's role assignments to be just the Garden scoped one (i.e. no
        # System scoped role assignments)
        user_with_role_assignments.role_assignments = [role_assignment_for_garden_scope]
        user_with_role_assignments.clear_permissions_cache()

        assert user_has_permission_for_object(
            user_with_role_assignments, "system:read", test_system_1_0_0
        )

    def test_user_has_permission_for_object_supports_brewtils_models(
        self,
        test_garden,
        test_system_1_0_0,
        user_with_role_assignments,
    ):
        """user_has_permission_for_object returns the appropriate results for brewtils
        model objects"""
        brewtils_garden = to_brewtils(test_garden)
        brewtils_system = to_brewtils(test_system_1_0_0)

        assert user_has_permission_for_object(
            user_with_role_assignments, "garden:read", brewtils_garden
        )
        assert user_has_permission_for_object(
            user_with_role_assignments, "request:create", brewtils_system
        )

        user_with_role_assignments.role_assignments = []
        user_with_role_assignments.clear_permissions_cache()

        assert not user_has_permission_for_object(
            user_with_role_assignments, "garden:read", brewtils_garden
        )
        assert not user_has_permission_for_object(
            user_with_role_assignments, "system:read", brewtils_system
        )

    def test_user_permitted_objects_returns_permitted_gardens(
        self, user_with_role_assignments, test_garden
    ):
        permitted_gardens = user_permitted_objects(
            user_with_role_assignments, Garden, "garden:read"
        )

        assert test_garden in permitted_gardens

    def test_user_permitted_objects_returns_permitted_gardens_via_global(
        self, user_with_role_assignments, test_garden
    ):
        permitted_gardens = user_permitted_objects(
            user_with_role_assignments, Garden, "garden:create"
        )

        assert test_garden in permitted_gardens

    def test_user_permitted_objects_does_not_return_nonpermitted_gardens(
        self, user_with_role_assignments, test_garden
    ):
        permitted_gardens = user_permitted_objects(
            user_with_role_assignments, Garden, "unassigned_permission"
        )

        assert test_garden not in permitted_gardens

    def test_user_permitted_objects_returns_permitted_systems(
        self, user_with_role_assignments, test_system_1_0_0, test_system_2_0_0
    ):
        permitted_systems = user_permitted_objects(
            user_with_role_assignments, System, "request:read"
        )

        assert test_system_1_0_0 in permitted_systems
        assert test_system_2_0_0 in permitted_systems

    def test_user_permitted_objects_does_not_return_nonpermitted_systems(
        self, user_with_role_assignments, test_garden
    ):
        permitted_systems = user_permitted_objects(
            user_with_role_assignments, System, "unassigned_permission"
        )

        assert test_system_1_0_0 not in permitted_systems
        assert test_system_2_0_0 not in permitted_systems

    def test_user_permitted_objects_returns_permitted_jobs(
        self, user_with_role_assignments, test_garden, test_job
    ):
        permitted_jobs = user_permitted_objects(
            user_with_role_assignments, Job, "job:read"
        )

        assert test_job in permitted_jobs

    def test_user_permitted_objects_does_not_return_nonpermitted_jobs(
        self, user_with_role_assignments, test_garden, test_job
    ):
        permitted_jobs = user_permitted_objects(
            user_with_role_assignments, Job, "unassigned_permission"
        )

        assert test_job not in permitted_jobs

    def test_user_permitted_objects_returns_permitted_requests(
        self, user_with_role_assignments, test_garden, test_request
    ):
        permitted_requests = user_permitted_objects(
            user_with_role_assignments, Request, "request:read"
        )

        assert test_request in permitted_requests
