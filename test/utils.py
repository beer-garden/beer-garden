import unittest

from functools import partial

import brewtils.schemas
from bg_utils.mongo.parser import MongoParser
from brewtils.schema_parser import SchemaParser
from brewtils.test.comparable import assert_system_equal


def convert(model, parser=None):
    schema = getattr(brewtils.schemas, model.schema)
    return parser._do_parse(
        SchemaParser._do_serialize(schema(), model, True),
        schema(),
        True,
    )


mongo2brew = partial(convert, parser=SchemaParser)
brew2mongo = partial(convert, parser=MongoParser)


def test_convert(bg_system):
    mongo = brew2mongo(bg_system)
    brew = mongo2brew(mongo)

    assert_system_equal(brew, bg_system)


class TestUtils(unittest.TestCase):
    def _assert_systems_equal(
        self, expected_system, test_system, include_commands=True
    ):
        self.assertEqual(expected_system.id, test_system.id)
        self.assertEqual(expected_system.name, test_system.name)
        self.assertEqual(expected_system.version, test_system.version)
        self.assertEqual(expected_system.description, test_system.description)
        self.assertEqual(expected_system.max_instances, test_system.max_instances)
        self.assertEqual(expected_system.icon_name, test_system.icon_name)
        self.assertEqual(len(expected_system.instances), len(test_system.instances))

        if include_commands:
            self.assertEqual(len(expected_system.commands), len(test_system.commands))
