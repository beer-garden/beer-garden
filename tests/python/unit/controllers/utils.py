import unittest


class TestUtils(unittest.TestCase):

    def _assert_systems_equal(self, expected_system, test_system, include_commands=True):
        self.assertEqual(expected_system.id, test_system.id)
        self.assertEqual(expected_system.name, test_system.name)
        self.assertEqual(expected_system.version, test_system.version)
        self.assertEqual(expected_system.description, test_system.description)
        self.assertEqual(expected_system.max_instances, test_system.max_instances)
        self.assertEqual(expected_system.icon_name, test_system.icon_name)
        self.assertEqual(len(expected_system.instances), len(test_system.instances))

        if include_commands:
            self.assertEqual(len(expected_system.commands), len(test_system.commands))
