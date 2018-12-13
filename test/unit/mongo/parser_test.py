import copy
import unittest
from datetime import datetime

from bg_utils.mongo.fields import StatusInfo
from bg_utils.mongo.models import Instance, AppState
from bg_utils.mongo.parser import MongoParser
from brewtils.errors import BrewmasterModelValidationError


class ParserTest(unittest.TestCase):
    def setUp(self):
        self.parser = MongoParser()

        self.serialized_app_state = {
            "versions": {"foo": "bar"},
            "auth": {"initialized": False},
        }
        self.serialized_instance_dict = {
            "id": "584f11af55a38e64799fd1d4",
            "name": "default",
            "description": "desc",
            "status": "RUNNING",
            "icon_name": "icon!",
            "queue_info": {
                "type": "rabbitmq",
                "queue": "echo[default]-0.0.1",
                "url": "amqp://guest:guest@localhost:5672/",
            },
            "status_info": {"heartbeat": 1451606400000},
        }
        self.instance = Instance(
            id="584f11af55a38e64799fd1d4",
            name="default",
            description="desc",
            status="RUNNING",
            icon_name="icon!",
            status_info=StatusInfo(heartbeat=datetime(2016, 1, 1)),
            queue_info={
                "type": "rabbitmq",
                "queue": "echo[default]-0.0.1",
                "url": "amqp://guest:guest@localhost:5672/",
            },
        )
        self.app_state = AppState(versions={"foo": "bar"}, auth={"initialized": False})

    def test_parse_none(self):
        self.assertRaises(
            BrewmasterModelValidationError,
            self.parser.parse_instance,
            None,
            from_string=True,
        )
        self.assertRaises(
            BrewmasterModelValidationError,
            self.parser.parse_instance,
            None,
            from_string=False,
        )

    def test_parse_empty(self):
        self.parser.parse_instance({}, from_string=False)
        self.parser.parse_instance("{}", from_string=True)

    def test_parse_error(self):
        self.assertRaises(
            BrewmasterModelValidationError,
            self.parser.parse_instance,
            "",
            from_string=True,
        )
        self.assertRaises(
            BrewmasterModelValidationError,
            self.parser.parse_instance,
            "bad bad bad",
            from_string=True,
        )

    def test_parse_bad_input_type(self):
        self.assertRaises(
            BrewmasterModelValidationError,
            self.parser.parse_instance,
            ["list", "bad"],
            from_string=True,
        )
        self.assertRaises(
            BrewmasterModelValidationError,
            self.parser.parse_instance,
            {"bad": "bad"},
            from_string=True,
        )

    def test_parse_fail_validation(self):
        self.serialized_instance_dict["name"] = None
        self.assertRaises(
            BrewmasterModelValidationError,
            self.parser.parse_instance,
            self.serialized_instance_dict,
        )
        self.assertRaises(
            BrewmasterModelValidationError,
            self.parser.parse_instance,
            "bad bad bad",
            from_string=False,
        )

    def test_parse_non_strict_failure(self):
        self.serialized_instance_dict["name"] = None
        self.parser.parse_instance(
            self.serialized_instance_dict, from_string=False, strict=False
        )

    def test_no_modify_arguments(self):
        instance_copy = copy.deepcopy(self.serialized_instance_dict)
        self.parser.parse_instance(self.serialized_instance_dict)
        self.assertEqual(instance_copy, self.serialized_instance_dict)

    def test_parse_instance_empty(self):
        parsed_instance = self.parser.parse_instance({})

        self.assertIsInstance(parsed_instance, Instance)
        self.assertEqual("default", parsed_instance.name)
        self.assertEqual("INITIALIZING", parsed_instance.status)
        self.assertIsNone(parsed_instance.id)
        self.assertIsNone(parsed_instance.description)
        self.assertIsNone(parsed_instance.icon_name)
        self.assertEqual({}, parsed_instance.queue_info)
        self.assertIsNone(parsed_instance.status_info.heartbeat)

    def test_parse_instance_full(self):
        parsed_instance = self.parser.parse_instance(self.serialized_instance_dict)

        self.assertIsInstance(parsed_instance, Instance)
        self.assertEqual(self.instance.id, parsed_instance.id)
        self.assertEqual(self.instance.name, parsed_instance.name)
        self.assertEqual(self.instance.description, parsed_instance.description)
        self.assertEqual(self.instance.status, parsed_instance.status)
        self.assertEqual(self.instance.icon_name, parsed_instance.icon_name)
        self.assertDictEqual(self.instance.queue_info, parsed_instance.queue_info)
        self.assertEqual(
            self.instance.status_info.heartbeat, parsed_instance.status_info.heartbeat
        )

    def test_parse_command_empty(self):
        pass

    def test_parse_parameter(self):
        pass

    def test_parse_request(self):
        pass

    # Serialize methods
    def test_serialize_system(self):
        pass

    def test_serialize_instance_empty(self):
        instance = self.parser.serialize_instance(Instance(), to_string=False)

        self.assertIsNone(instance["id"])
        self.assertIsNone(instance["description"])
        self.assertIsNone(instance["icon_name"])
        self.assertEqual("default", instance["name"])
        self.assertEqual("INITIALIZING", instance["status"])
        self.assertDictEqual({}, instance["queue_info"])

        # This is different than BREWTILS
        self.assertDictEqual({"heartbeat": None}, instance["status_info"])

    def test_serialize_instance_full(self):
        instance = self.parser.serialize_instance(self.instance, to_string=False)

        self.assertEqual(self.serialized_instance_dict["id"], instance["id"])
        self.assertEqual(self.serialized_instance_dict["name"], instance["name"])
        self.assertEqual(
            self.serialized_instance_dict["description"], instance["description"]
        )
        self.assertEqual(self.serialized_instance_dict["status"], instance["status"])
        self.assertEqual(
            self.serialized_instance_dict["icon_name"], instance["icon_name"]
        )
        self.assertDictEqual(
            self.serialized_instance_dict["queue_info"], instance["queue_info"]
        )
        self.assertDictEqual(
            self.serialized_instance_dict["status_info"], instance["status_info"]
        )

    def test_serialize_command(self):
        pass

    def test_serialize_parameter(self):
        pass

    def test_serialize_request(self):
        pass

    def test_serialize_app_state(self):
        self.assertEqual(
            self.parser.serialize_app_state(self.app_state, to_string=False),
            self.serialized_app_state,
        )

    def test_parse_app_state(self):
        state = self.parser.parse_app_state(self.serialized_app_state)
        self.assertDictEqual(state.versions, self.serialized_app_state["versions"])
        self.assertDictEqual(state.auth, self.serialized_app_state["auth"])
