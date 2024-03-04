import pytest
from mongoengine import connect

from brewtils.models import User, Role

from beer_garden.authorization import QueryFilterBuilder, ModelFilter, check_global_roles, generate_permission_levels, _has_empty_scopes

# @pytest.fixture(autouse=True)
# def drop():
#     Garden.drop_collection()
#     Role.drop_collection()
#     System.drop_collection()
#     User.drop_collection()


@pytest.fixture()
def role_for_global_scope():
    role = Role(name="global", permission="ADMIN")

    yield role

@pytest.fixture()
def role_for_read_scope():
    role = Role(name="read", permission="READ_ONLY")

    yield role


@pytest.fixture()
def user_for_global_scope(role_for_global_scope):
    user = User(username="global", roles=["global"], local_roles=[role_for_global_scope])
    yield user

@pytest.fixture()
def user_for_read_scope(role_for_read_scope):
    user = User(username="read", roles=["read"], local_roles=[role_for_read_scope])
    yield user


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
        assert generate_permission_levels("READ_ONLY") == ["READ_ONLY","OPERATOR","ADMIN"]
        assert generate_permission_levels("OPERATOR") == ["OPERATOR","ADMIN"]
        assert generate_permission_levels("ADMIN") == ["ADMIN"]

    def test__has_empty_scopes(self):
        assert _has_empty_scopes(Role(name="test", scope_gardens=[""], scope_namespaces=[""], scope_systems=[""], scope_instances=[""], scope_versions=[""], scope_commands=[""]), [])
        
        assert _has_empty_scopes(Role(name="test", scope_gardens=[""], scope_namespaces=[""], scope_systems=[""], scope_instances=[""], scope_versions=[""], scope_commands=[]), ["scope_commands"])
        assert not _has_empty_scopes(Role(name="test", scope_gardens=[""], scope_namespaces=[""], scope_systems=[""], scope_instances=[""], scope_versions=[""], scope_commands=[""]), ["scope_commands"])
        
        assert _has_empty_scopes(Role(name="test", scope_gardens=[""], scope_namespaces=[""], scope_systems=[""], scope_instances=[""], scope_versions=[], scope_commands=[""]), ["scope_versions"])
        assert not _has_empty_scopes(Role(name="test", scope_gardens=[""], scope_namespaces=[""], scope_systems=[""], scope_instances=[""], scope_versions=[""], scope_commands=[""]), ["scope_versions"])

        assert _has_empty_scopes(Role(name="test", scope_gardens=[""], scope_namespaces=[""], scope_systems=[""], scope_instances=[], scope_versions=[""], scope_commands=[""]), ["scope_instances"])
        assert not _has_empty_scopes(Role(name="test", scope_gardens=[""], scope_namespaces=[""], scope_systems=[""], scope_instances=[""], scope_versions=[""], scope_commands=[""]), ["scope_instances"])

        assert _has_empty_scopes(Role(name="test", scope_gardens=[""], scope_namespaces=[""], scope_systems=[], scope_instances=[""], scope_versions=[""], scope_commands=[""]), ["scope_systems"])
        assert not _has_empty_scopes(Role(name="test", scope_gardens=[""], scope_namespaces=[""], scope_systems=[""], scope_instances=[""], scope_versions=[""], scope_commands=[""]), ["scope_systems"])

        assert _has_empty_scopes(Role(name="test", scope_gardens=[""], scope_namespaces=[], scope_systems=[""], scope_instances=[""], scope_versions=[""], scope_commands=[""]), ["scope_namespaces"])
        assert not _has_empty_scopes(Role(name="test", scope_gardens=[""], scope_namespaces=[""], scope_systems=[""], scope_instances=[""], scope_versions=[""], scope_commands=[""]), ["scope_namespaces"])

        assert _has_empty_scopes(Role(name="test", scope_gardens=[], scope_namespaces=[""], scope_systems=[""], scope_instances=[""], scope_versions=[""], scope_commands=[""]), ["scope_gardens"])
        assert not _has_empty_scopes(Role(name="test", scope_gardens=[""], scope_namespaces=[""], scope_systems=[""], scope_instances=[""], scope_versions=[""], scope_commands=[""]), ["scope_gardens"])
        
        