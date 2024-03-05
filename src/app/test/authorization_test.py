import pytest
from mongoengine import connect

from brewtils.models import User, Role, Request, Garden, System, Instance, Command

from beer_garden.authorization import (
    QueryFilterBuilder,
    ModelFilter,
    check_global_roles,
    generate_permission_levels,
    _has_empty_scopes,
)

# @pytest.fixture(autouse=True)
# def drop():
#     Garden.drop_collection()
#     Role.drop_collection()
#     System.drop_collection()
#     User.drop_collection()


@pytest.fixture()
def role_for_global_scope():
    role = Role(name="global", permission="ADMIN")

    return role


@pytest.fixture()
def role_for_read_scope():
    role = Role(name="read", permission="READ_ONLY")

    return role


@pytest.fixture()
def user_for_global_scope(role_for_global_scope):
    user = User(
        username="global", roles=["global"], local_roles=[role_for_global_scope]
    )
    return user


@pytest.fixture()
def user_for_read_scope(role_for_read_scope):
    user = User(username="read", roles=["read"], local_roles=[role_for_read_scope])
    return user


@pytest.fixture()
def query_filter():
    return QueryFilterBuilder()


@pytest.fixture()
def model_filter():
    return ModelFilter()


@pytest.fixture()
def base_request():
    return Request(
        requester="user1",
        namespace="namespace",
        system="system",
        system_version="1",
        instance_name="instance",
        command="command",
    )

@pytest.fixture()
def base_command():
    return Command(name="command")

@pytest.fixture()
def base_instance():
    return Instance(name="instance")

@pytest.fixture()
def base_system(base_command, base_instance):
    return System(name="system", namespace="namespace", version="1", instances=[base_instance], commands=[base_command])

@pytest.fixture()
def base_garden(base_system):
    return Garden(name="garden", systems=[base_system])


class TestAuthorization:
    def test_query_filter_global_check(self, user_for_global_scope):
        """get_garden should allow for retrieval by name"""
        assert check_global_roles(user_for_global_scope, permission_level="ADMIN")
        assert check_global_roles(user_for_global_scope, permission_level="OPERATOR")
        assert check_global_roles(user_for_global_scope, permission_level="READ_ONLY")

    def test_query_filter_read_check(self, user_for_read_scope):
        """get_garden should allow for retrieval by name"""
        assert not check_global_roles(user_for_read_scope, permission_level="ADMIN")
        assert not check_global_roles(user_for_read_scope, permission_level="OPERATOR")
        assert check_global_roles(user_for_read_scope, permission_level="READ_ONLY")

    def test_generate_permission_levels(self):
        assert generate_permission_levels("READ_ONLY") == [
            "READ_ONLY",
            "OPERATOR",
            "ADMIN",
        ]
        assert generate_permission_levels("OPERATOR") == ["OPERATOR", "ADMIN"]
        assert generate_permission_levels("ADMIN") == ["ADMIN"]

    def test__has_empty_scopes(self):
        assert _has_empty_scopes(
            Role(
                name="test",
                scope_gardens=[""],
                scope_namespaces=[""],
                scope_systems=[""],
                scope_instances=[""],
                scope_versions=[""],
                scope_commands=[""],
            ),
            [],
        )

        assert _has_empty_scopes(
            Role(
                name="test",
                scope_gardens=[""],
                scope_namespaces=[""],
                scope_systems=[""],
                scope_instances=[""],
                scope_versions=[""],
                scope_commands=[],
            ),
            ["scope_commands"],
        )
        assert not _has_empty_scopes(
            Role(
                name="test",
                scope_gardens=[""],
                scope_namespaces=[""],
                scope_systems=[""],
                scope_instances=[""],
                scope_versions=[""],
                scope_commands=[""],
            ),
            ["scope_commands"],
        )

        assert _has_empty_scopes(
            Role(
                name="test",
                scope_gardens=[""],
                scope_namespaces=[""],
                scope_systems=[""],
                scope_instances=[""],
                scope_versions=[],
                scope_commands=[""],
            ),
            ["scope_versions"],
        )
        assert not _has_empty_scopes(
            Role(
                name="test",
                scope_gardens=[""],
                scope_namespaces=[""],
                scope_systems=[""],
                scope_instances=[""],
                scope_versions=[""],
                scope_commands=[""],
            ),
            ["scope_versions"],
        )

        assert _has_empty_scopes(
            Role(
                name="test",
                scope_gardens=[""],
                scope_namespaces=[""],
                scope_systems=[""],
                scope_instances=[],
                scope_versions=[""],
                scope_commands=[""],
            ),
            ["scope_instances"],
        )
        assert not _has_empty_scopes(
            Role(
                name="test",
                scope_gardens=[""],
                scope_namespaces=[""],
                scope_systems=[""],
                scope_instances=[""],
                scope_versions=[""],
                scope_commands=[""],
            ),
            ["scope_instances"],
        )

        assert _has_empty_scopes(
            Role(
                name="test",
                scope_gardens=[""],
                scope_namespaces=[""],
                scope_systems=[],
                scope_instances=[""],
                scope_versions=[""],
                scope_commands=[""],
            ),
            ["scope_systems"],
        )
        assert not _has_empty_scopes(
            Role(
                name="test",
                scope_gardens=[""],
                scope_namespaces=[""],
                scope_systems=[""],
                scope_instances=[""],
                scope_versions=[""],
                scope_commands=[""],
            ),
            ["scope_systems"],
        )

        assert _has_empty_scopes(
            Role(
                name="test",
                scope_gardens=[""],
                scope_namespaces=[],
                scope_systems=[""],
                scope_instances=[""],
                scope_versions=[""],
                scope_commands=[""],
            ),
            ["scope_namespaces"],
        )
        assert not _has_empty_scopes(
            Role(
                name="test",
                scope_gardens=[""],
                scope_namespaces=[""],
                scope_systems=[""],
                scope_instances=[""],
                scope_versions=[""],
                scope_commands=[""],
            ),
            ["scope_namespaces"],
        )

        assert _has_empty_scopes(
            Role(
                name="test",
                scope_gardens=[],
                scope_namespaces=[""],
                scope_systems=[""],
                scope_instances=[""],
                scope_versions=[""],
                scope_commands=[""],
            ),
            ["scope_gardens"],
        )
        assert not _has_empty_scopes(
            Role(
                name="test",
                scope_gardens=[""],
                scope_namespaces=[""],
                scope_systems=[""],
                scope_instances=[""],
                scope_versions=[""],
                scope_commands=[""],
            ),
            ["scope_gardens"],
        )


class TestModelFilter:
    def test_get_user_filter(
        self, model_filter, user_for_read_scope, user_for_global_scope
    ):
        assert model_filter._get_user_filter(
            user_for_read_scope, user_for_read_scope, ["ADMIN"]
        )

        assert not model_filter._get_user_filter(
            user_for_global_scope, user_for_read_scope, ["ADMIN"]
        )
        assert model_filter._get_user_filter(
            user_for_global_scope, user_for_read_scope, ["READ_ONLY"]
        )

        assert model_filter._get_user_filter(
            user_for_global_scope, user_for_global_scope, ["ADMIN"]
        )
        assert model_filter._get_user_filter(
            user_for_read_scope, user_for_global_scope, ["ADMIN"]
        )

    def test_get_role_filter(
        self,
        model_filter,
        user_for_read_scope,
        user_for_global_scope,
        role_for_global_scope,
    ):
        assert model_filter._get_role_filter(
            user_for_read_scope.local_roles[0], user_for_read_scope, ["READ_ONLY"]
        )
        assert not model_filter._get_role_filter(
            role_for_global_scope, user_for_read_scope, ["READ_ONLY"]
        )

        assert model_filter._get_role_filter(
            role_for_global_scope, user_for_global_scope, ["READ_ONLY"]
        )

    @pytest.mark.parametrize(
        "user,returned",
        [
            (User(username="user1"), True),
            (User(username="user2"), False),
            (
                User(
                    username="user2",
                    local_roles=[
                        Role(permission="ADMIN", name="role", scope_gardens=["garden"])
                    ],
                ),
                True,
            ),
            (
                User(
                    username="user2",
                    local_roles=[
                        Role(permission="ADMIN", name="role", scope_gardens=["garden2"])
                    ],
                ),
                False,
            ),
            (
                User(
                    username="user2",
                    local_roles=[
                        Role(
                            permission="ADMIN",
                            name="role",
                            scope_gardens=["garden"],
                            scope_namespaces=["namespace"],
                        )
                    ],
                ),
                True,
            ),
            (
                User(
                    username="user2",
                    local_roles=[
                        Role(
                            permission="ADMIN",
                            name="role",
                            scope_gardens=["garden"],
                            scope_namespaces=["namespace2"],
                        )
                    ],
                ),
                False,
            ),
            (
                User(
                    username="user2",
                    local_roles=[
                        Role(
                            permission="ADMIN",
                            name="role",
                            scope_gardens=["garden"],
                            scope_systems=["system"],
                        )
                    ],
                ),
                True,
            ),
            (
                User(
                    username="user2",
                    local_roles=[
                        Role(
                            permission="ADMIN",
                            name="role",
                            scope_gardens=["garden"],
                            scope_systems=["system2"],
                        )
                    ],
                ),
                False,
            ),
            (
                User(
                    username="user2",
                    local_roles=[
                        Role(
                            permission="ADMIN",
                            name="role",
                            scope_gardens=["garden"],
                            scope_versions=["1"],
                        )
                    ],
                ),
                True,
            ),
            (
                User(
                    username="user2",
                    local_roles=[
                        Role(
                            permission="ADMIN",
                            name="role",
                            scope_gardens=["garden"],
                            scope_versions=["2"],
                        )
                    ],
                ),
                False,
            ),
            (
                User(
                    username="user2",
                    local_roles=[
                        Role(
                            permission="ADMIN",
                            name="role",
                            scope_gardens=["garden"],
                            scope_instances=["instance"],
                        )
                    ],
                ),
                True,
            ),
            (
                User(
                    username="user2",
                    local_roles=[
                        Role(
                            permission="ADMIN",
                            name="role",
                            scope_gardens=["garden"],
                            scope_instances=["instance2"],
                        )
                    ],
                ),
                False,
            ),
            (
                User(
                    username="user2",
                    local_roles=[
                        Role(
                            permission="ADMIN",
                            name="role",
                            scope_gardens=["garden"],
                            scope_commands=["command"],
                        )
                    ],
                ),
                True,
            ),
            (
                User(
                    username="user2",
                    local_roles=[
                        Role(
                            permission="ADMIN",
                            name="role",
                            scope_gardens=["garden"],
                            scope_commands=["command2"],
                        )
                    ],
                ),
                False,
            ),
            (
                User(
                    username="user2",
                    local_roles=[
                        Role(
                            permission="ADMIN",
                            name="role",
                            scope_gardens=["garden"],
                            scope_commands=["command2"],
                        )
                    ],
                    remote_roles=[
                        Role(
                            permission="ADMIN",
                            name="role2",
                            scope_gardens=["garden"],
                            scope_versions=["2"],
                        )
                    ],
                ),
                False,
            ),
            (
                User(
                    username="user2",
                    local_roles=[
                        Role(
                            permission="ADMIN",
                            name="role",
                            scope_gardens=["garden", "garden2", "garden3"],
                        )
                    ],
                ),
                True,
            ),
            (
                User(
                    username="user2",
                    local_roles=[
                        Role(
                            permission="ADMIN",
                            name="role",
                            scope_gardens=["garden", "garden2", "garden3"],
                            scope_namespaces=["namespace", "namespace2"],
                            scope_systems=["system", "system2"],
                            scope_instances=["instance", "instance2"],
                            scope_versions=["1", "2"],
                            scope_commands=["command2"],
                        )
                    ],
                ),
                False,
            ),
            (
                User(
                    username="user2",
                    local_roles=[
                        Role(
                            permission="ADMIN",
                            name="role",
                            scope_gardens=["garden", "garden2", "garden3"],
                            scope_namespaces=["namespace", "namespace2"],
                            scope_systems=["system", "system2"],
                            scope_instances=["instance", "instance2"],
                            scope_versions=["1", "2"],
                            scope_commands=["command", "command2"],
                        )
                    ],
                ),
                True,
            ),
        ],
    )
    def test_get_request_filter(self, model_filter, base_request, user, returned):
        if returned:
            assert model_filter._get_request_filter(
                base_request, user, ["ADMIN"], source_garden="garden"
            )

        else:
            assert not model_filter._get_request_filter(
                base_request, user, ["ADMIN"], source_garden="garden"
            )


    
    @pytest.mark.parametrize(
        "user,returned",    
        [
            (User(
                    username="user2",
                    local_roles=[
                        Role(
                            permission="ADMIN",
                            name="role",
                            scope_gardens=["garden", "garden2", "garden3"],
                            scope_namespaces=["namespace", "namespace2"],
                            scope_systems=["system", "system2"],
                            scope_instances=["instance", "instance2"],
                            scope_versions=["1", "2"],
                            scope_commands=["command", "command2"],
                        )
                    ],
                ),
                True
            ),
            (User(
                    username="user2",
                    local_roles=[
                        Role(
                            permission="ADMIN",
                            name="role",
                            scope_gardens=["garden2", "garden3"],
                            scope_namespaces=["namespace", "namespace2"],
                            scope_systems=["system", "system2"],
                            scope_instances=["instance", "instance2"],
                            scope_versions=["1", "2"],
                            scope_commands=["command", "command2"],
                        )
                    ],
                ),
                False)
        ]
    )
    def test_get_garden_filter(self, model_filter, base_garden, user, returned):
        if returned:
            assert model_filter._get_garden_filter(
                base_garden, user, ["ADMIN"],
            )

        else:
            assert not model_filter._get_garden_filter(
                base_garden, user, ["ADMIN"]
            )


    # @pytest.mark.parametrize(
    #     "user,returned",    
    #     [
    #         (User(
    #                 username="user2",
    #                 local_roles=[
    #                     Role(
    #                         permission="ADMIN",
    #                         name="role",
    #                         scope_gardens=["garden"],
    #                         scope_namespaces=["namespace"],
    #                         scope_systems=["system"],
    #                         scope_instances=["instance"],
    #                         scope_versions=["1"],
    #                         scope_commands=["command"],
    #                     )
    #                 ],
    #             ),
    #             True
    #         ),
    #         (User(
    #                 username="user2",
    #                 local_roles=[
    #                     Role(
    #                         permission="ADMIN",
    #                         name="role",
    #                         scope_gardens=["garden", "garden2", "garden3"],
    #                         scope_namespaces=["namespace", "namespace2"],
    #                         scope_systems=["system2"],
    #                         scope_instances=["instance", "instance2"],
    #                         scope_versions=["1", "2"],
    #                         scope_commands=["command", "command2"],
    #                     )
    #                 ],
    #             ),
    #             False)
    #     ]
    # )
    # def test_get_garden_filter_check_systems(self, model_filter, base_garden, user, returned):
    #     if returned:
    #         assert model_filter._get_garden_filter(
    #             base_garden, user, ["ADMIN"],
    #         ).systems

    #         assert model_filter.filter_object(
    #             base_garden, user, ["ADMIN"]
    #         )
    #     else:
    #         assert not model_filter._get_garden_filter(
    #             base_garden, user, ["ADMIN"]
    #         ).systems
    #         assert not model_filter.filter_object(
    #             base_garden, user, ["ADMIN"]
    #         ).systems
            
    
    @pytest.mark.parametrize(
        "user,returned",    
        [
            (User(
                    username="user2",
                    local_roles=[
                        Role(
                            permission="ADMIN",
                            name="role",
                            scope_gardens=["garden", "garden2", "garden3"],
                            scope_namespaces=["namespace", "namespace2"],
                            scope_systems=["system", "system2"],
                            scope_instances=["instance", "instance2"],
                            scope_versions=["1", "2"],
                            scope_commands=["command", "command2"],
                        )
                    ],
                ),
                True
            ),
            (User(
                    username="user2",
                    local_roles=[
                        Role(
                            permission="ADMIN",
                            name="role",
                            scope_gardens=["garden", "garden2", "garden3"],
                            scope_namespaces=["namespace", "namespace2"],
                            scope_systems=["system", "system2"],
                            scope_instances=["instance", "instance2"],
                            scope_versions=["1", "2"],
                            scope_commands=["command2"],
                        )
                    ],
                ),
                False)
        ]
    )
    def test_get_command_filter(self, model_filter, base_command, base_system, user, returned):
        if returned:
            assert model_filter._get_command_filter(
                base_command, user, ["ADMIN"], source_system=base_system, source_garden_name="garden"
            )
        else:
            assert not model_filter._get_command_filter(
                base_command, user, ["ADMIN"], source_system=base_system, source_garden_name="garden"
            )

    @pytest.mark.parametrize(
        "user,returned",    
        [
            (User(
                    username="user2",
                    local_roles=[
                        Role(
                            permission="ADMIN",
                            name="role",
                            scope_gardens=["garden", "garden2", "garden3"],
                            scope_namespaces=["namespace", "namespace2"],
                            scope_systems=["system", "system2"],
                            scope_instances=["instance", "instance2"],
                            scope_versions=["1", "2"],
                            scope_commands=["command", "command2"],
                        )
                    ],
                ),
                True
            ),
            (User(
                    username="user2",
                    local_roles=[
                        Role(
                            permission="ADMIN",
                            name="role",
                            scope_gardens=["garden", "garden2", "garden3"],
                            scope_namespaces=["namespace", "namespace2"],
                            scope_systems=["system", "system2"],
                            scope_instances=["instance2"],
                            scope_versions=["1", "2"],
                            scope_commands=["command", "command2"],
                        )
                    ],
                ),
                False)
        ]
    )
    def test_get_instance_filter(self, model_filter, base_instance, base_system, user, returned):
        if returned:
            assert model_filter._get_instance_filter(
                base_instance, user, ["ADMIN"], source_system=base_system, source_garden_name="garden"
            )
        else:
            assert not model_filter._get_instance_filter(
                base_instance, user, ["ADMIN"], source_system=base_system, source_garden_name="garden"
            )

    @pytest.mark.parametrize(
        "user,returned",    
        [
            (User(
                    username="user2",
                    local_roles=[
                        Role(
                            permission="ADMIN",
                            name="role",
                            scope_gardens=["garden", "garden2", "garden3"],
                            scope_namespaces=["namespace", "namespace2"],
                            scope_systems=["system", "system2"],
                            scope_instances=["instance", "instance2"],
                            scope_versions=["1", "2"],
                            scope_commands=["command", "command2"],
                        )
                    ],
                ),
                True
            ),
            (User(
                    username="user2",
                    local_roles=[
                        Role(
                            permission="ADMIN",
                            name="role",
                            scope_gardens=["garden", "garden2", "garden3"],
                            scope_namespaces=["namespace", "namespace2"],
                            scope_systems=["system2"],
                            scope_instances=["instance", "instance2"],
                            scope_versions=["1", "2"],
                            scope_commands=["command", "command2"],
                        )
                    ],
                ),
                False)
        ]
    )
    def test_get_system_filter(self, model_filter, base_system, user, returned):
        if returned:
            assert model_filter._get_system_filter(
                base_system, user, ["ADMIN"], source_garden_name="garden"
            )
        else:
            assert not model_filter._get_system_filter(
                base_system, user, ["ADMIN"], source_garden_name="garden"
            )
