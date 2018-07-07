import unittest
from datetime import datetime

import mongoengine
import pytest
import pytz
from mock import Mock, PropertyMock, patch

from bg_utils.models import Command, Instance, Parameter, Request, System, Choices, Job, \
    DateTrigger, IntervalTrigger, CronTrigger
from brewtils.errors import BrewmasterModelValidationError
from brewtils.schemas import RequestTemplateSchema


class CommandTest(unittest.TestCase):

    def test_str(self):
        c = Command(name='foo', description='bar', parameters=[])
        self.assertEqual('foo', str(c))

    def test_repr(self):
        c = Command(name='foo', description='bar', parameters=[])
        self.assertEqual('<Command: foo>', repr(c))

    def test_clean(self):
        Command(name='foo', parameters=[Parameter(key='foo', optional=False)]).clean()

    def test_clean_empty_name(self):
        command = Command(name='')
        self.assertRaises(BrewmasterModelValidationError, command.clean)

    def test_clean_fail_bad_command_type(self):
        command = Command(name='foo', description='bar', command_type='BAD TYPE', parameters=[])
        self.assertRaises(BrewmasterModelValidationError, command.clean)

    def test_clean_fail_bad_output_type(self):
        command = Command(name='foo', description='bar', output_type='BAD TYPE', parameters=[])
        self.assertRaises(BrewmasterModelValidationError, command.clean)

    def test_clean_fail_duplicate_parameter_keys(self):
        parameter = Parameter(key='foo', optional=False)
        command = Command(name='foo', parameters=[parameter, parameter])
        self.assertRaises(BrewmasterModelValidationError, command.clean)


class InstanceTest(unittest.TestCase):

    def test_str(self):
        self.assertEqual('name', str(Instance(name='name')))

    def test_repr(self):
        instance = Instance(name='name', status='RUNNING')
        self.assertNotEqual(-1, repr(instance).find('name'))
        self.assertNotEqual(-1, repr(instance).find('RUNNING'))

    def test_clean_bad_status(self):
        instance = Instance(status='BAD')
        self.assertRaises(BrewmasterModelValidationError, instance.clean)


class ChoicesTest(unittest.TestCase):

    def test_str(self):
        self.assertEqual('value', str(Choices(value='value')))

    def test_repr(self):
        choices = Choices(type='static', display='select', strict=True, value=[1])
        self.assertNotEqual(-1, repr(choices).find('static'))
        self.assertNotEqual(-1, repr(choices).find('select'))
        self.assertNotEqual(-1, repr(choices).find('[1]'))

    def test_clean_value_types(self):
        self.assertRaises(BrewmasterModelValidationError, Choices(type='static',
                                                                  value='SHOULD_BE_A_LIST').clean)
        self.assertRaises(BrewmasterModelValidationError, Choices(type='url', value=[1, 2]).clean)
        self.assertRaises(BrewmasterModelValidationError, Choices(type='command',
                                                                  value=[1, 2]).clean)

    def test_clean_missing_dict_keys(self):
        self.assertRaises(BrewmasterModelValidationError, Choices(type='command',
                                                                  value={'command': 'foo'}).clean)

    def test_clean_static(self):
        choice = Choices(type='static', value=['a', 'b', 'c'])
        choice.clean()
        self.assertEqual({}, choice.details)

    @patch('bg_utils.models.parse')
    def test_clean_parse(self, parse_mock):
        choice = Choices(type='command', value='foo')
        choice.clean()

        self.assertTrue(parse_mock.called)
        self.assertNotEqual({}, choice.details)

    @patch('bg_utils.models.parse')
    def test_clean_with_details(self, parse_mock):
        choice = Choices(type='command', value='foo', details={'non': 'empty'})
        choice.clean()

        self.assertFalse(parse_mock.called)
        self.assertNotEqual({}, choice.details)

    def test_clean_bad_parse(self):
        command_dict = {'command': 'foo${arg', 'system': 'foo', 'version': '1.0.0',
                        'instance_name': 'default'}

        self.assertRaises(BrewmasterModelValidationError,
                          Choices(type='command', value=command_dict['command']).clean)
        self.assertRaises(BrewmasterModelValidationError,
                          Choices(type='command', value=command_dict).clean)
        self.assertRaises(BrewmasterModelValidationError,
                          Choices(type='url', value='http://foo?arg=${val').clean)


class ParameterTest(unittest.TestCase):

    def test_str(self):
        p = Parameter(key='foo', description='bar', type='Boolean', optional=False)
        self.assertEqual('foo', str(p))

    def test_repr(self):
        p = Parameter(key='foo', description='bar', type='Boolean', optional=False)
        self.assertEqual('<Parameter: key=foo, type=Boolean, description=bar>', repr(p))

    def test_default_display_name(self):
        p = Parameter(key='foo')
        self.assertEqual(p.display_name, 'foo')

    def test_clean(self):
        Parameter(key='foo', optional=False).clean()

    def test_clean_fail_nullable_optional_but_no_default(self):
        p = Parameter(key='foo', optional=True, default=None, nullable=False)
        self.assertRaises(BrewmasterModelValidationError, p.clean)

    def test_clean_fail_duplicate_parameter_keys(self):
        nested = Parameter(key='foo')
        p = Parameter(key='foo', optional=False, parameters=[nested, nested])

        self.assertRaises(BrewmasterModelValidationError, p.clean)


class RequestTest(unittest.TestCase):

    def test_str(self):
        self.assertEqual('command', str(Request(command='command')))

    def test_repr(self):
        request = Request(command='command', status='CREATED')
        self.assertNotEqual(-1, repr(request).find('name'))
        self.assertNotEqual(-1, repr(request).find('CREATED'))

    def test_clean_fail_bad_status(self):
        request = Request(system='foo', command='bar', status='bad')
        self.assertRaises(BrewmasterModelValidationError, request.clean)

    def test_clean_fail_bad_command_type(self):
        request = Request(system='foo', command='bar', command_type='BAD')
        self.assertRaises(BrewmasterModelValidationError, request.clean)

    def test_clean_fail_bad_output_type(self):
        request = Request(system='foo', command='bar', output_type='BAD')
        self.assertRaises(BrewmasterModelValidationError, request.clean)

    @patch('bg_utils.models.Request.objects')
    def test_find_one_or_none_found(self, objects_mock):
        self.assertEqual(objects_mock.get.return_value, Request.find_or_none('id'))

    @patch('bg_utils.models.Request.objects')
    def test_find_one_or_none_none_found(self, objects_mock):
        objects_mock.get = Mock(side_effect=mongoengine.DoesNotExist)
        self.assertIsNone(Request.find_or_none('id'))

    @patch('mongoengine.Document.save', Mock())
    def test_save_update_updated_at(self):
        request = Request(system='foo', command='bar', status='CREATED',
                          updated_at='this_will_be_updated')
        request.save()
        self.assertNotEqual(request.updated_at, 'this_will_be_updated')

    def test_template_check(self):
        self.assertEqual(
            len(Request.TEMPLATE_FIELDS),
            len(RequestTemplateSchema.get_attribute_names())
        )


class SystemTest(unittest.TestCase):

    def setUp(self):
        self.default_command = Command(name='name', description='description')
        self.default_command.save = Mock()
        self.default_command.validate = Mock()
        self.default_command.delete = Mock()

        self.default_instance = Instance(name='default')
        self.default_instance.save = Mock()
        self.default_instance.validate = Mock()
        self.default_instance.delete = Mock()

        self.default_system = System(id='1234', name='foo', version='1.0.0',
                                     instances=[self.default_instance],
                                     commands=[self.default_command])
        self.default_system.save = Mock()
        self.default_system.validate = Mock()
        self.default_system.delete = Mock()

    def tearDown(self):
        self.default_system = None

    def test_str(self):
        self.assertEqual('foo-1.0.0', str(self.default_system))

    def test_repr(self):
        self.assertNotEqual(-1, repr(self.default_system).find('foo'))
        self.assertNotEqual(-1, repr(self.default_system).find('1.0.0'))

    def test_clean(self):
        self.default_system.clean()

    def test_clean_fail_max_instances(self):
        self.default_system.instances.append(Instance(name='default2'))
        self.assertRaises(BrewmasterModelValidationError, self.default_system.clean)

    def test_clean_fail_duplicate_instance_names(self):
        self.default_system.max_instances = 2
        self.default_system.instances.append(Instance(name='default'))
        self.assertRaises(BrewmasterModelValidationError, self.default_system.clean)

    @patch('bg_utils.models.System.objects')
    def test_find_unique_system(self, objects_mock):
        objects_mock.get = Mock(return_value=self.default_system)
        self.assertEqual(self.default_system, System.find_unique('foo', '1.0.0'))

    @patch('bg_utils.models.System.objects', Mock(get=Mock(side_effect=mongoengine.DoesNotExist)))
    def test_find_unique_system_none(self):
        self.assertIsNone(System.find_unique('foo', '1.0.0'))

    def test_deep_save(self):
        self.default_system.deep_save()
        self.assertEqual(self.default_system.save.call_count, 2)
        self.assertEqual(len(self.default_system.commands), 1)
        self.assertEqual(self.default_command.system, self.default_system)
        self.assertEqual(self.default_command.save.call_count, 1)
        self.assertEqual(self.default_instance.save.call_count, 1)

    def test_deep_save_validate_exception(self):
        self.default_command.validate = Mock(side_effect=ValueError)

        self.assertRaises(ValueError, self.default_system.deep_save)
        self.assertEqual(self.default_system.commands, [self.default_command])
        self.assertEqual(self.default_system.instances, [self.default_instance])
        self.assertFalse(self.default_command.save.called)
        self.assertFalse(self.default_instance.save.called)
        self.assertFalse(self.default_system.delete.called)

    @patch('bg_utils.models.Command.validate', Mock())
    @patch('bg_utils.models.Instance.validate', Mock())
    def test_deep_save_save_exception(self):
        self.default_instance.save = Mock(side_effect=ValueError)

        self.assertRaises(ValueError, self.default_system.deep_save)
        self.assertEqual(self.default_system.commands, [self.default_command])
        self.assertEqual(self.default_system.instances, [self.default_instance])
        self.assertTrue(self.default_command.save.called)
        self.assertTrue(self.default_instance.save.called)
        self.assertFalse(self.default_system.delete.called)

    @patch('bg_utils.models.Command.validate', Mock())
    @patch('bg_utils.models.Instance.validate', Mock())
    def test_deep_save_save_exception_not_already_exists(self):
        self.default_instance.save = Mock(side_effect=ValueError)

        with patch('bg_utils.models.System.id', new_callable=PropertyMock) as id_mock:
            id_mock.side_effect = [None, '1234', '1234']
            self.assertRaises(ValueError, self.default_system.deep_save)

        self.assertEqual(self.default_system.commands, [self.default_command])
        self.assertEqual(self.default_system.instances, [self.default_instance])
        self.assertTrue(self.default_command.save.called)
        self.assertTrue(self.default_instance.save.called)
        self.assertTrue(self.default_system.delete.called)

    def test_deep_delete(self):
        self.default_system.deep_delete()
        self.assertEqual(self.default_system.delete.call_count, 1)
        self.assertEqual(self.default_command.delete.call_count, 1)
        self.assertEqual(self.default_instance.delete.call_count, 1)

    # FYI - Have to mock out System.commands here or else MongoEngine
    # blows up trying to dereference them
    @patch('bg_utils.models.System.commands', Mock())
    @patch('bg_utils.models.Command.objects')
    def test_upsert_commands_new(self, objects_mock):
        self.default_system.commands = []
        objects_mock.return_value = []
        new_command = Mock()

        self.default_system.upsert_commands([new_command])
        self.assertTrue(new_command.save.called)
        self.assertTrue(self.default_system.save.called)
        self.assertEqual([new_command], self.default_system.commands)

    @patch('bg_utils.models.System.commands', Mock())
    @patch('bg_utils.models.Command.objects')
    def test_upsert_commands_delete(self, objects_mock):
        old_command = Mock()
        objects_mock.return_value = [old_command]

        self.default_system.upsert_commands([])
        self.assertTrue(old_command.delete.called)
        self.assertEqual([], self.default_system.commands)

    @patch('bg_utils.models.System.commands', Mock())
    @patch('bg_utils.models.Command.objects')
    def test_upsert_commands_update(self, objects_mock):
        new_command = Mock(description='new desc')
        old_command = Mock(id='123', description='old desc')
        name_mock = PropertyMock(return_value='name')
        type(new_command).name = name_mock
        type(old_command).name = name_mock

        objects_mock.return_value = [old_command]

        self.default_system.upsert_commands([new_command])
        self.assertTrue(self.default_system.save.called)
        self.assertTrue(new_command.save.called)
        self.assertFalse(old_command.delete.called)
        self.assertEqual([new_command], self.default_system.commands)
        self.assertEqual(old_command.id, self.default_system.commands[0].id)
        self.assertEqual(new_command.description, self.default_system.commands[0].description)


class JobTest(unittest.TestCase):

    def test_invalid_trigger_type(self):
        job = Job(trigger_type='INVALID_TRIGGER_TYPE')
        with self.assertRaises(BrewmasterModelValidationError):
            job.clean()

    def test_trigger_mismatch(self):
        date_trigger = DateTrigger()
        job = Job(trigger_type='cron', trigger=date_trigger)
        with self.assertRaises(BrewmasterModelValidationError):
            job.clean()


class TriggerTest(unittest.TestCase):

    def setUp(self):
        self.interval = IntervalTrigger()
        self.cron = CronTrigger()
        self.date = DateTrigger(run_date=datetime.now())

    def test_scheduler_kwargs_interval(self):
        expected = {
            'weeks': 0,
            'days': 0,
            'hours': 0,
            'minutes': 0,
            'seconds': 0,
            'start_date': None,
            'end_date': None,
            'timezone': pytz.utc,
            'jitter': None,
        }
        self.assertEqual(self.interval.get_scheduler_kwargs(), expected)

        self.interval.start_date = datetime.now()
        start_date = self.interval.get_scheduler_kwargs()['start_date']
        self.assertEqual(start_date.tzinfo, pytz.utc)

    def test_scheduler_kwargs_cron(self):
        expected = {
            'year': '*',
            'month': '1',
            'day': '1',
            'week': '*',
            'day_of_week': '*',
            'hour': '0',
            'minute': '0',
            'second': '0',
            'start_date': None,
            'end_date': None,
            'timezone': pytz.utc,
            'jitter': None,
        }
        self.assertEqual(self.cron.get_scheduler_kwargs(), expected)

        self.cron.start_date = datetime.now()
        start_date = self.cron.get_scheduler_kwargs()['start_date']
        self.assertEqual(start_date.tzinfo, pytz.utc)

    def test_scheduler_kwargs_date(self):
        expected = {
            'run_date': pytz.utc.localize(self.date.run_date),
            'timezone': pytz.utc,
        }
        self.assertEqual(self.date.get_scheduler_kwargs(), expected)

        self.date.run_date = datetime.now()
        start_date = self.date.get_scheduler_kwargs()['run_date']
        self.assertEqual(start_date.tzinfo, pytz.utc)
