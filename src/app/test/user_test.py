# -*- coding: utf-8 -*-
from brewtils.models import (
    Role,
    User,
    Garden,
    System,
    Command,
    Instance,
    RemoteUserMap,
)

from brewtils.schema_parser import SchemaParser


from beer_garden.user import (
    flatten_user_role,
    remote_role_match_garden,
    generate_remote_user,
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

    def test_remote_role_match_garden(self):
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

        assert remote_role_match_garden(role_1, garden_1)
        assert not remote_role_match_garden(role_1, garden_2)
        assert not remote_role_match_garden(role_1, garden_3)

        assert not remote_role_match_garden(role_2, garden_1)
        assert remote_role_match_garden(role_2, garden_2)
        assert remote_role_match_garden(role_2, garden_3)

        assert remote_role_match_garden(role_3, garden_1)
        assert remote_role_match_garden(role_3, garden_2)
        assert remote_role_match_garden(role_3, garden_3)

        assert remote_role_match_garden(role_4, garden_1)
        assert remote_role_match_garden(role_4, garden_2)
        assert remote_role_match_garden(role_4, garden_3)

        assert not remote_role_match_garden(role_5, garden_1)
        assert remote_role_match_garden(role_5, garden_2)
        assert remote_role_match_garden(role_5, garden_3)

    def test_generate_remote_user(self):
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
            remote_user_mapping=[
                RemoteUserMap(target_garden="A", username="USER1"),
                RemoteUserMap(target_garden="B", username="USER2"),
            ],
        )

        remote_user_1 = generate_remote_user(garden_1, local_user)
        assert remote_user_1.username == "USER1"
        assert len(remote_user_1.local_roles) == 0
        assert len(remote_user_1.remote_roles) == 1
        assert len(remote_user_1.remote_user_mapping) == 0

        remote_user_2 = generate_remote_user(garden_2, local_user)
        assert remote_user_2.username == "USER2"
        assert len(remote_user_2.local_roles) == 0
        assert len(remote_user_2.remote_roles) == 2
        assert len(remote_user_2.remote_user_mapping) == 1
        assert remote_user_2.remote_user_mapping[0].target_garden == "A"
        assert remote_user_2.remote_user_mapping[0].username == "USER1"

        remote_user_3 = generate_remote_user(garden_3, local_user)
        assert remote_user_3.username == local_user.username
        assert len(remote_user_3.local_roles) == 0
        assert len(remote_user_3.remote_roles) == len(local_user.local_roles)
        assert len(remote_user_3.remote_user_mapping) == len(
            local_user.remote_user_mapping
        )
