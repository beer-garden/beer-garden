import unittest

from mock import Mock, patch
from mongoengine.connection import connect, disconnect, get_connection

from bg_utils.mongo.models import System


class SystemIntegrationTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        connect('test_bg_utils')

    @classmethod
    def tearDownClass(cls):
        connection = get_connection()
        connection.drop_database('test_bg_utils')
        disconnect('test_bg_utils')

    def setUp(self):
        self.default_system = System(name='foo', version='1.0.0')

    def tearDown(self):
        self.default_system = None
        System.drop_collection()

    @patch('mongoengine.queryset.QuerySet.filter', Mock(return_value=[1]))
    def find_unique_system(self):
        system = System.find_unique('foo', '0.0.0')
        assert system == 1

    @patch('mongoengine.queryset.QuerySet.get', Mock(return_value=[]))
    def find_unique_system_none(self):
        system = System.find_unique('foo', '1.0.0')
        assert system is None

    # def test_system_non_unique_name(self):
    #     s = System(name='foo', control_system='bar', instance_names=['only'])
    #     System.ensure_indexes()
    #     s.save()
    #     s2 = System(name='foo', control_system='bar', instance_names=['only'])
    #     self.assertRaises(mongoengine.NotUniqueError, s2.save)
    #
    # def test_system_non_unique_instance_names(self):
    #     s = System(name='foo', control_system='bar',
    #                instance_names=['oops', 'oops'])
    #     System.ensure_indexes()
    #     self.assertRaises(mongoengine.NotUniqueError, s.save)
    #
    # def test_default_instance_name(self):
    #     # s = System(name='foo')
    #     System.ensure_indexes()
    #     self.default_system.save()
    #     assert self.default_system.instances == []
