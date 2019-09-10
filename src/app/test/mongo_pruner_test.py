import unittest
from datetime import timedelta

from mock import MagicMock, Mock, patch

from beer_garden.mongo_pruner import MongoPruner


class MongoPrunerTest(unittest.TestCase):
    def setUp(self):
        self.mongo_pruner = MongoPruner(tasks=None)

        self.collection_mock = MagicMock(__name__="MOCK")
        self.field_mock = "test"
        self.delete_after_mock = timedelta(microseconds=1)
        self.additional_query_mock = Mock()

        self.task = {
            "collection": self.collection_mock,
            "field": self.field_mock,
            "delete_after": self.delete_after_mock,
            "additional_query": self.additional_query_mock,
        }

        self.mongo_pruner.add_task(**self.task)

    @patch("bartender.mongo_pruner.Q", MagicMock())
    def test_prune_something(self):
        self.mongo_pruner._stop_event = Mock(wait=Mock(side_effect=[False, True]))

        self.mongo_pruner.run()
        self.assertTrue(self.collection_mock.objects.return_value.delete.called)
