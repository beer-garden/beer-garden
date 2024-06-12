# -*- coding: utf-8 -*-
from brewtils.models import Command, Garden, Instance, AliasUserMap, Role, System, User
from brewtils.schema_parser import SchemaParser

from beer_garden.user import (
    flatten_user_role,
    generate_downstream_user,
    upstream_role_match_garden,
)


class TestUser:

    def test_flatten_user_role(self):
        role = Role(
            name="test",
            scope_gardens=["A", "B"],
            scope_systems=["foo", "bar"],
            scope_commands=["command1", "command2"],
        )
        flatten_roles = []
        flatten_user_role(role, flatten_roles)

        assert len(flatten_roles) == 8
        valid_roles = [
            SchemaParser.serialize_role(
                Role(
                    name="test",
                    scope_gardens=["A"],
                    scope_systems=["foo"],
                    scope_commands=["command1"],
                )
            ),
            SchemaParser.serialize_role(
                Role(
                    name="test",
                    scope_gardens=["B"],
                    scope_systems=["foo"],
                    scope_commands=["command1"],
                )
            ),
            SchemaParser.serialize_role(
                Role(
                    name="test",
                    scope_gardens=["A"],
                    scope_systems=["bar"],
                    scope_commands=["command1"],
                )
            ),
            SchemaParser.serialize_role(
                Role(
                    name="test",
                    scope_gardens=["B"],
                    scope_systems=["bar"],
                    scope_commands=["command1"],
                )
            ),
            SchemaParser.serialize_role(
                Role(
                    name="test",
                    scope_gardens=["A"],
                    scope_systems=["foo"],
                    scope_commands=["command2"],
                )
            ),
            SchemaParser.serialize_role(
                Role(
                    name="test",
                    scope_gardens=["B"],
                    scope_systems=["foo"],
                    scope_commands=["command2"],
                )
            ),
            SchemaParser.serialize_role(
                Role(
                    name="test",
                    scope_gardens=["A"],
                    scope_systems=["bar"],
                    scope_commands=["command2"],
                )
            ),
            SchemaParser.serialize_role(
                Role(
                    name="test",
                    scope_gardens=["B"],
                    scope_systems=["bar"],
                    scope_commands=["command2"],
                )
            ),
        ]

        for flatten_role in flatten_roles:
            assert SchemaParser.serialize_role(flatten_role) in valid_roles

    def test_flatten_user_role_no_change(self):
        role = Role(
            name="test",
            scope_gardens=["A"],
            scope_systems=["foo"],
            scope_commands=["command1"],
        )
        flatten_roles = flatten_user_role(role, [])

        assert len(flatten_roles) == 1
        assert SchemaParser.serialize_role(
            flatten_roles[0]
        ) == SchemaParser.serialize_role(
            Role(
                name="test",
                scope_gardens=["A"],
                scope_systems=["foo"],
                scope_commands=["command1"],
            )
        )

    def test_upstream_role_match_garden(self):
        role_1 = Role(
            name="test_1",
            scope_gardens=["A"],
            scope_systems=["foo"],
            scope_commands=["command1"],
        )
        role_2 = Role(name="test_2", scope_systems=["bar"])
        role_3 = Role(name="test_3")
        role_4 = Role(name="test_3", scope_versions=["1"])
        role_5 = Role(name="test_3", scope_instances=["beta"])

        garden_1 = Garden(
            name="A",
            systems=[
                System(
                    name="foo",
                    instances=[Instance(name="alpha")],
                    version="1",
                    commands=[Command(name="command1")],
                )
            ],
        )
        garden_2 = Garden(
            name="B",
            systems=[
                System(
                    name="bar",
                    instances=[Instance(name="beta")],
                    version="1",
                    commands=[Command(name="command2")],
                )
            ],
        )
        garden_3 = Garden(name="C")

        assert upstream_role_match_garden(role_1, garden_1)
        assert not upstream_role_match_garden(role_1, garden_2)
        assert not upstream_role_match_garden(role_1, garden_3)

        assert not upstream_role_match_garden(role_2, garden_1)
        assert upstream_role_match_garden(role_2, garden_2)
        assert upstream_role_match_garden(role_2, garden_3)

        assert upstream_role_match_garden(role_3, garden_1)
        assert upstream_role_match_garden(role_3, garden_2)
        assert upstream_role_match_garden(role_3, garden_3)

        assert upstream_role_match_garden(role_4, garden_1)
        assert upstream_role_match_garden(role_4, garden_2)
        assert upstream_role_match_garden(role_4, garden_3)

        assert not upstream_role_match_garden(role_5, garden_1)
        assert upstream_role_match_garden(role_5, garden_2)
        assert upstream_role_match_garden(role_5, garden_3)

    def test_generate_downstream_user(self):
        garden_1 = Garden(
            name="A",
            systems=[
                System(
                    name="foo",
                    instances=[Instance(name="alpha")],
                    version="1",
                    commands=[Command(name="command1")],
                )
            ],
        )
        garden_2 = Garden(
            name="B",
            children=[garden_1],
            systems=[
                System(
                    name="bar",
                    instances=[Instance(name="beta")],
                    version="1",
                    commands=[Command(name="command2")],
                )
            ],
        )
        garden_3 = Garden(name="C", shared_users=True)

        local_user = User(
            username="test",
            local_roles=[
                Role(
                    name="test_1",
                    scope_gardens=["A"],
                    scope_systems=["foo"],
                    scope_commands=["command1"],
                ),
                Role(
                    name="test_2",
                    scope_systems=["bar"],
                    scope_commands=["command1", "command2"],
                ),
            ],
            alias_user_mapping=[
                AliasUserMap(target_garden="A", username="USER1"),
                AliasUserMap(target_garden="B", username="USER2"),
            ],
        )

        downstream_user_1 = generate_downstream_user(garden_1, local_user)
        assert downstream_user_1.username == "USER1"
        assert len(downstream_user_1.local_roles) == 0
        assert len(downstream_user_1.upstream_roles) == 1
        assert len(downstream_user_1.alias_user_mapping) == 0

        downstream_user_2 = generate_downstream_user(garden_2, local_user)
        assert downstream_user_2.username == "USER2"
        assert len(downstream_user_2.local_roles) == 0
        assert len(downstream_user_2.upstream_roles) == 2
        assert len(downstream_user_2.alias_user_mapping) == 1
        assert downstream_user_2.alias_user_mapping[0].target_garden == "A"
        assert downstream_user_2.alias_user_mapping[0].username == "USER1"

        downstream_user_3 = generate_downstream_user(garden_3, local_user)
        assert downstream_user_3.username == local_user.username
        assert len(downstream_user_3.local_roles) == 0
        assert len(downstream_user_3.upstream_roles) == len(local_user.local_roles)
        assert len(downstream_user_3.alias_user_mapping) == len(
            local_user.alias_user_mapping
        )
