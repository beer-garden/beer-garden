"""Testing for the Mongo version of the SchemaParser

I migrated this to pytest but the only tests here were for Instances. I didn't add
tests for the other models because I'm not convinced it's worth the effort. At this
point the MongoParser is just the SchemaParser that parses into a different type. So a
lot of the tests here are really testing marshmallow (trying to parse a string with
from_string=False or something) or mongoengine (testing that an empty dictionary parses
into the correct default values).

"""

import pytest
from pytest_lazyfixture import lazy_fixture

from beer_garden.bg_utils.mongo.models import Instance
from beer_garden.bg_utils.mongo.parser import MongoParser
from brewtils.errors import ModelValidationError
from brewtils.test.comparable import assert_instance_equal


@pytest.fixture
def parser():
    return MongoParser()


@pytest.mark.parametrize(
    "method,data,kwargs,assertion,expected",
    [
        (
            "parse_instance",
            lazy_fixture("instance_dict"),
            {},
            assert_instance_equal,
            lazy_fixture("mongo_instance"),
        )
    ],
)
def test_parse(parser, method, data, kwargs, assertion, expected):
    actual = getattr(parser, method)(data, **kwargs)

    # Mongo just compares the objectIDs...
    assert actual == expected

    # ...so also do the brewtils assertion
    assertion(expected, actual)


class TestInstance(object):
    def test_parse_empty(self, parser):
        parser.parse_instance({}, from_string=False)
        parser.parse_instance("{}", from_string=True)

    @pytest.mark.parametrize("from_string", [True, False])
    def test_parse_none(self, parser, from_string):
        with pytest.raises(ModelValidationError):
            parser.parse_instance(None, from_string=from_string)

    @pytest.mark.parametrize(
        "parse_value", ["", "bad bad bad", ["list", "bad"], {"bad": "bad"}]
    )
    def test_parse_bad_inputs(self, parser, parse_value):
        with pytest.raises(ModelValidationError):
            parser.parse_instance(parse_value, from_string=True)

    def test_parse_missing_name(self, parser, instance_dict):
        instance_dict["name"] = None
        with pytest.raises(ModelValidationError):
            parser.parse_instance(instance_dict)

    def test_parse_missing_name_non_strict(self, parser, instance_dict):
        instance_dict["name"] = None
        parser.parse_instance(instance_dict, strict=False)

    def test_parse_instance_empty(self, parser):
        parsed_instance = parser.parse_instance({})

        assert isinstance(parsed_instance, Instance)
        assert parsed_instance.name == "default"
        assert parsed_instance.status == "INITIALIZING"
        assert parsed_instance.queue_info == {}
        assert parsed_instance.id is None
        assert parsed_instance.description is None
        assert parsed_instance.icon_name is None
        assert parsed_instance.icon_name is None
        assert parsed_instance.status_info.heartbeat is None

    def test_serialize_default_instance(self, parser):
        serialized_instance = parser.serialize_instance(Instance(), to_string=False)

        assert serialized_instance["id"] is None
        assert serialized_instance["description"] is None
        assert serialized_instance["icon_name"] is None
        assert serialized_instance["name"] == "default"
        assert serialized_instance["status"] == "INITIALIZING"
        assert serialized_instance["queue_info"] == {}

        # Different than Brewtils
        assert serialized_instance["status_info"] == {"heartbeat": None}

    def test_serialize_instance_full(self, parser, mongo_instance, instance_dict):
        serialized_instance = parser.serialize_instance(mongo_instance, to_string=False)

        for key in [
            "id",
            "name",
            "description",
            "status",
            "icon_name",
            "queue_info",
            "status_info",
        ]:
            assert serialized_instance[key] == instance_dict[key]
