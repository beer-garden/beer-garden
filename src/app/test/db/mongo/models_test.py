# -*- coding: utf-8 -*-
import copy

import pytest
from brewtils.errors import ModelValidationError, RequestStatusTransitionError
from brewtils.schemas import RequestTemplateSchema
from mock import Mock
from mongoengine import NotUniqueError, ValidationError, connect

import beer_garden.db.api as db
import beer_garden.db.mongo.models
from beer_garden.api.authorization import Permissions
from beer_garden.db.mongo.models import (
    Choices,
    Command,
    DateTrigger,
    Garden,
    Instance,
    Job,
    Parameter,
    Request,
    Role,
    RoleAssignment,
    System,
    User,
)


class TestCommand(object):
    def test_str(self):
        assert str(Command(name="foo", parameters=[])) == "foo"

    def test_repr(self):
        c = Command(name="foo", description="bar", parameters=[])
        assert repr(c) == "<Command: foo>"

    def test_clean(self):
        Command(name="foo", parameters=[Parameter(key="foo", optional=False)]).clean()

    @pytest.mark.parametrize(
        "params",
        [
            {"name": ""},
            {"name": "foo", "command_type": "BAD", "parameters": []},
            {"name": "foo", "output_type": "BAD", "parameters": []},
        ],
    )
    def test_clean_empty_name(self, params):
        with pytest.raises(ModelValidationError):
            Command(**params).clean()

    def test_clean_fail_duplicate_parameter_keys(self):
        parameter = Parameter(key="foo", optional=False)
        command = Command(name="foo", parameters=[parameter, parameter])

        with pytest.raises(ModelValidationError):
            command.clean()


class TestInstance(object):
    def test_str(self):
        assert str(Instance(name="name")) == "name"

    def test_repr(self):
        instance = Instance(name="name", status="RUNNING")
        assert "name" in repr(instance)
        assert "RUNNING" in repr(instance)

    def test_clean_bad_status(self):
        with pytest.raises(ModelValidationError):
            Instance(status="BAD").clean()


class TestChoices(object):
    def test_str(self):
        assert str(Choices(value="value")) == "value"

    def test_repr(self):
        choices = Choices(type="static", display="select", strict=True, value=[1])
        assert "static" in repr(choices)
        assert "select" in repr(choices)
        assert "[1]" in repr(choices)

    @pytest.mark.parametrize(
        "choice_obj",
        [
            Choices(type="static", value="SHOULD_BE_A_LIST"),
            Choices(type="url", value=[1, 2]),
            Choices(type="command", value=[1, 2]),
            Choices(type="command", value={"command": "foo"}),
        ],
    )
    def test_clean_value_types(self, choice_obj):
        with pytest.raises(ModelValidationError):
            choice_obj.clean()

    def test_clean_static(self):
        choice = Choices(type="static", value=["a", "b", "c"])
        choice.clean()
        assert choice.details == {}

    def test_clean_parse(self):
        choice = Choices(type="command", value="foo")
        choice.clean()
        assert choice.details == {"name": "foo", "args": []}

    def test_clean_with_details(self):
        choice = Choices(type="command", value="foo", details={"non": "empty"})
        choice.clean()

        assert choice.details == {"non": "empty"}

    @pytest.mark.parametrize(
        "value",
        [
            "foo${arg",
            "http://foo?arg=${val",
            {
                "command": "foo${arg",
                "system": "foo",
                "version": "1.0.0",
                "instance_name": "default",
            },
        ],
    )
    def test_clean_bad_parse(self, value):
        with pytest.raises(ModelValidationError):
            Choices(type="command", value=value).clean()


class TestParameter(object):
    def test_str(self):
        p = Parameter(key="foo", description="bar", type="Boolean", optional=False)
        assert str(p) == "foo"

    def test_repr(self):
        p = Parameter(key="foo", description="bar", type="Boolean", optional=False)
        assert repr(p) == "<Parameter: key=foo, type=Boolean, description=bar>"

    def test_default_display_name(self):
        p = Parameter(key="foo")
        assert p.display_name == "foo"

    def test_clean(self):
        Parameter(key="foo", optional=False).clean()

    def test_clean_fail_nullable_optional_but_no_default(self):
        with pytest.raises(ModelValidationError):
            Parameter(key="foo", optional=True, default=None, nullable=False).clean()

    def test_clean_fail_duplicate_parameter_keys(self):
        nested = Parameter(key="foo")
        with pytest.raises(ModelValidationError):
            Parameter(key="foo", optional=False, parameters=[nested, nested]).clean()


class TestRequest(object):
    @pytest.fixture(autouse=True)
    def drop(self, mongo_conn):
        Request.drop_collection()

    def test_str(self):
        assert str(Request(command="command")) == "command"

    def test_repr(self):
        request = Request(command="command", status="CREATED")
        assert "name" in repr(request)
        assert "CREATED" in repr(request)

    class TestClean:
        @pytest.mark.parametrize(
            "req",
            [
                Request(system="foo", command="bar", status="bad"),
                Request(system="foo", command="bar", command_type="BAD"),
                Request(system="foo", command="bar", output_type="BAD"),
            ],
        )
        def test_bad_values(self, req):
            with pytest.raises(ModelValidationError):
                req.clean()

        @pytest.mark.parametrize(
            "parent, has_parent",
            [(None, False), ("something", True)],
        )
        def test_set_has_parent(self, parent, has_parent):
            req = Request(command="bar", parent=parent)
            req.clean()
            assert req.has_parent is has_parent

        @pytest.mark.parametrize(
            "parent, has_parent",
            [(None, True), (Request(command="say"), False)],
        )
        def test_parent_mismatch(self, parent, has_parent):
            req = Request(command="bar", parent=parent, has_parent=has_parent)
            with pytest.raises(ModelValidationError):
                req.clean()

    class TestCleanUpdate:
        @pytest.mark.parametrize(
            "start, end",
            [
                ("SUCCESS", "IN_PROGRESS"),
                ("SUCCESS", "ERROR"),
                ("IN_PROGRESS", "CREATED"),
            ],
        )
        def test_invalid_transitions(self, bg_request, start, end):
            bg_request.status = start
            bg_request.output = None

            db.create(bg_request)

            with pytest.raises(RequestStatusTransitionError):
                bg_request.status = end
                db.update(bg_request)

    # TODO - Make these integration tests
    # @patch("bg_utils.mongo.models.Request.objects")
    # def test_find_one_or_none_found(self, objects_mock):
    #     self.assertEqual(objects_mock.get.return_value, Request.find_or_none("id"))
    #
    # @patch("bg_utils.mongo.models.Request.objects")
    # def test_find_one_or_none_none_found(self, objects_mock):
    #     objects_mock.get = Mock(side_effect=mongoengine.DoesNotExist)
    #     self.assertIsNone(Request.find_or_none("id"))
    #
    # @patch("mongoengine.Document.save", Mock())
    # def test_save_update_updated_at(self):
    #     request = Request(
    #         system="foo",
    #         command="bar",
    #         status="CREATED",
    #         updated_at="this_will_be_updated",
    #     )
    #     request.save()
    #     self.assertNotEqual(request.updated_at, "this_will_be_updated")

    # Namespace was removed from the TEMPLATE_FIELDS list, so reduce by one
    def test_template_check(self):
        assert len(Request.TEMPLATE_FIELDS) == len(
            RequestTemplateSchema.get_attribute_names()
        )

    @pytest.fixture()
    def request_model(self):
        req = Request(
            system="foo",
            command="bar",
            status="CREATED",
            system_version="1.0.0",
            instance_name="foobar",
            namespace="barfoo",
        )
        req.parameters = {"message": "hi"}
        req.output = "bye"
        req.parameters_gridfs.put = Mock()
        req.output_gridfs.put = Mock()
        return req

    @pytest.fixture()
    def max_size(self, monkeypatch):
        """mock max request size to be arbitrarily small"""
        monkeypatch.setattr(beer_garden.db.mongo.models, "REQUEST_MAX_PARAM_SIZE", 100)
        return beer_garden.db.mongo.models.REQUEST_MAX_PARAM_SIZE + 10

    def test_save_stores_in_gridfs_after_maxsize(self, request_model, max_size):
        request_model.parameters = {"message": "a" * max_size}
        request_model.output = "a" * max_size
        request_model.save()

        request_model.parameters_gridfs.put.assert_called_once()
        request_model.output_gridfs.put.assert_called_once()

    def test_save_retains_if_under_maxsize(self, request_model, max_size):
        request_model.save()

        request_model.parameters_gridfs.put.assert_not_called()
        request_model.output_gridfs.put.assert_not_called()

    def test_save_retains_only_parameters(self, request_model, max_size):
        request_model.output = "a" * max_size
        request_model.save()

        request_model.parameters_gridfs.put.assert_not_called()
        request_model.output_gridfs.put.assert_called_once()

    def test_save_retains_only_output(self, request_model, max_size):
        request_model.parameters = {"message": "a" * max_size}
        request_model.save()

        request_model.parameters_gridfs.put.assert_called_once()
        request_model.output_gridfs.put.assert_not_called()

    def test_save_handles_bool(self, request_model, max_size):
        request_model.parameters = {"message": True}
        request_model.save()

        request_model.parameters_gridfs.put.assert_not_called()
        request_model.output_gridfs.put.assert_not_called()

    def test_save_preserves_status_updated_at_field(self, request_model):
        request_model.save()
        first_time = request_model.status_updated_at
        request_model.save()

        assert first_time == request_model.status_updated_at

    def test_status_changes_status_updated_at_field(self, request_model):
        request_model.save()
        first_time = request_model.status_updated_at
        request_model.status = "SUCCESS"
        request_model.save()

        assert first_time != request_model.status_updated_at


class TestSystem(object):
    @pytest.fixture(autouse=True)
    def drop(self, mongo_conn):
        System.drop_collection()

    @pytest.fixture
    def default_command(self):
        default_command = Command(name="name", description="description")
        default_command.save = Mock()
        default_command.validate = Mock()
        default_command.delete = Mock()

        return default_command

    @pytest.fixture
    def default_instance(self):
        default_instance = Instance(name="default")
        default_instance.save = Mock()
        default_instance.validate = Mock()
        default_instance.delete = Mock()

        return default_instance

    @pytest.fixture
    def default_system(self, default_command, default_instance):
        default_system = System(
            id="1234",
            name="foo",
            version="1.0.0",
            namespace="ns",
            instances=[default_instance],
            commands=[default_command],
        )
        default_system.save = Mock()
        default_system.validate = Mock()
        default_system.delete = Mock()

        return default_system

    def test_str(self, default_system):
        assert str(default_system) == "ns:foo-1.0.0"

    def test_repr(self, default_system):
        assert "ns" in repr(default_system)
        assert "foo" in repr(default_system)
        assert "1.0.0" in repr(default_system)

    def test_clean(self, default_system):
        default_system.clean()

    def test_clean_fail_max_instances(self, default_system):
        default_system.max_instances = 1
        default_system.instances.append(Instance(name="default2"))
        with pytest.raises(ModelValidationError):
            default_system.clean()

    def test_clean_fail_duplicate_instance_names(self, default_system):
        default_system.max_instances = 2
        default_system.instances.append(Instance(name="default"))
        with pytest.raises(ModelValidationError):
            default_system.clean()

    # TODO - These need to be integration tests
    # @patch("bg_utils.mongo.models.System.objects")
    # def test_find_unique_system(self, objects_mock):
    #     objects_mock.get = Mock(return_value=self.default_system)
    #     self.assertEqual(self.default_system, System.find_unique("foo", "1.0.0"))
    #
    # @patch(
    #     "bg_utils.mongo.models.System.objects",
    #     Mock(get=Mock(side_effect=mongoengine.DoesNotExist)),
    # )
    # def test_find_unique_system_none(self):
    #     self.assertIsNone(System.find_unique("foo", "1.0.0"))
    #
    # def test_deep_save(self, default_system):
    #     self.default_system.deep_save()
    #     self.assertEqual(self.default_system.save.call_count, 2)
    #     self.assertEqual(len(self.default_system.commands), 1)
    #     self.assertEqual(self.default_command.system, self.default_system)
    #     self.assertEqual(self.default_command.save.call_count, 1)
    #     self.assertEqual(self.default_instance.save.call_count, 1)
    #
    # def test_deep_save_validate_exception(self):
    #     self.default_command.validate = Mock(side_effect=ValueError)
    #
    #     self.assertRaises(ValueError, self.default_system.deep_save)
    #     self.assertEqual(self.default_system.commands, [self.default_command])
    #     self.assertEqual(self.default_system.instances, [self.default_instance])
    #     self.assertFalse(self.default_command.save.called)
    #     self.assertFalse(self.default_instance.save.called)
    #     self.assertFalse(self.default_system.delete.called)
    #
    # @patch("bg_utils.mongo.models.Command.validate", Mock())
    # @patch("bg_utils.mongo.models.Instance.validate", Mock())
    # def test_deep_save_save_exception(self):
    #     self.default_instance.save = Mock(side_effect=ValueError)
    #
    #     self.assertRaises(ValueError, self.default_system.deep_save)
    #     self.assertEqual(self.default_system.commands, [self.default_command])
    #     self.assertEqual(self.default_system.instances, [self.default_instance])
    #     self.assertTrue(self.default_command.save.called)
    #     self.assertTrue(self.default_instance.save.called)
    #     self.assertFalse(self.default_system.delete.called)
    #
    # @patch("bg_utils.mongo.models.Command.validate", Mock())
    # @patch("bg_utils.mongo.models.Instance.validate", Mock())
    # def test_deep_save_save_exception_not_already_exists(self):
    #     self.default_instance.save = Mock(side_effect=ValueError)
    #
    #     with patch(
    #         "bg_utils.mongo.models.System.id", new_callable=PropertyMock
    #     ) as id_mock:
    #         id_mock.side_effect = [None, "1234", "1234"]
    #         self.assertRaises(ValueError, self.default_system.deep_save)
    #
    #     self.assertEqual(self.default_system.commands, [self.default_command])
    #     self.assertEqual(self.default_system.instances, [self.default_instance])
    #     self.assertTrue(self.default_command.save.called)
    #     self.assertTrue(self.default_instance.save.called)
    #     self.assertTrue(self.default_system.delete.called)
    #
    # def test_deep_delete(self):
    #     self.default_system.deep_delete()
    #     self.assertEqual(self.default_system.delete.call_count, 1)
    #     self.assertEqual(self.default_command.delete.call_count, 1)
    #     self.assertEqual(self.default_instance.delete.call_count, 1)
    #
    # # FYI - Have to mock out System.commands here or else MongoEngine
    # # blows up trying to dereference them
    # @patch("bg_utils.mongo.models.System.commands", Mock())
    # @patch("bg_utils.mongo.models.Command.objects")
    # def test_upsert_commands_new(self, objects_mock):
    #     self.default_system.commands = []
    #     objects_mock.return_value = []
    #     new_command = Mock()
    #
    #     self.default_system.upsert_commands([new_command])
    #     self.assertTrue(new_command.save.called)
    #     self.assertTrue(self.default_system.save.called)
    #     self.assertEqual([new_command], self.default_system.commands)
    #
    # @patch("bg_utils.mongo.models.System.commands", Mock())
    # @patch("bg_utils.mongo.models.Command.objects")
    # def test_upsert_commands_delete(self, objects_mock):
    #     old_command = Mock()
    #     objects_mock.return_value = [old_command]
    #
    #     self.default_system.upsert_commands([])
    #     self.assertTrue(old_command.delete.called)
    #     self.assertEqual([], self.default_system.commands)
    #
    # @patch("bg_utils.mongo.models.System.commands", Mock())
    # @patch("bg_utils.mongo.models.Command.objects")
    # def test_upsert_commands_update(self, objects_mock):
    #     new_command = Mock(description="new desc")
    #     old_command = Mock(id="123", description="old desc")
    #     name_mock = PropertyMock(return_value="name")
    #     type(new_command).name = name_mock
    #     type(old_command).name = name_mock
    #
    #     objects_mock.return_value = [old_command]
    #
    #     self.default_system.upsert_commands([new_command])
    #     self.assertTrue(self.default_system.save.called)
    #     self.assertTrue(new_command.save.called)
    #     self.assertFalse(old_command.delete.called)
    #     self.assertEqual([new_command], self.default_system.commands)
    #     self.assertEqual(old_command.id, self.default_system.commands[0].id)
    #     self.assertEqual(
    #         new_command.description, self.default_system.commands[0].description
    #     )
    #
    # TODO - Same for these. They were actually in the integration test package
    # @patch("mongoengine.queryset.QuerySet.filter", Mock(return_value=[1]))
    # def find_unique_system(self):
    #     system = System.find_unique("foo", "0.0.0")
    #     assert system == 1
    #
    # @patch("mongoengine.queryset.QuerySet.get", Mock(return_value=[]))
    # def find_unique_system_none(self):
    #     system = System.find_unique("foo", "1.0.0")
    #     assert system is None
    #
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


class TestJob(object):
    @pytest.fixture(autouse=True)
    def drop(self, mongo_conn):
        Job.drop_collection()

    def test_invalid_trigger_type(self):
        with pytest.raises(ModelValidationError):
            Job(trigger_type="INVALID_TRIGGER_TYPE").clean()

    def test_trigger_mismatch(self):
        date_trigger = DateTrigger()
        with pytest.raises(ModelValidationError):
            Job(trigger_type="cron", trigger=date_trigger).clean()


class TestRole:
    @pytest.fixture(autouse=True)
    def drop(self, mongo_conn):
        Role.drop_collection()

    def test_create_with_valid_permissions(self):
        permissions = [Permissions.REQUEST_READ.value, Permissions.REQUEST_CREATE.value]

        role = Role(name="test_role", permissions=permissions)
        role.save()

        assert Role.objects.filter(name="test_role").count() == 1

    def test_create_with_invalid_permissions(self):
        permissions = ["invalid_permission"]

        role = Role(name="test_role", permissions=permissions)

        with pytest.raises(ValidationError):
            role.save()


class TestUser:
    @classmethod
    def setup_class(cls):
        connect("beer_garden", host="mongomock://localhost")

    @pytest.fixture()
    def role(self):
        role = Role(
            name="test_role", permissions=[Permissions.REQUEST_READ.value]
        ).save()

        yield role
        role.delete()

    @pytest.fixture()
    def role_assignment(self, role):
        return RoleAssignment(
            role=role,
            domain={"scope": "Garden", "identifiers": {"name": "test_garden"}},
        )

    @pytest.fixture()
    def role_assignment_missing_identifiers(self, role):
        return RoleAssignment(role=role, domain={"scope": "Garden"})

    @pytest.fixture()
    def user(self, role_assignment):
        user = User(username="testuser", role_assignments=[role_assignment]).save()

        yield user
        user.delete()

    def test_create(self, user):
        assert User.objects.filter(username="testuser").count() == 1

    def test_set_password(self, user):
        user.set_password("password")

        # Testing for a specific value would be too tightly coupled with the hashing
        # algorithm we use, so instead just verify that the password is not stored
        # in its original form
        assert user.password is not None
        assert user.password != "password"

    def test_verify_password(self, user):
        user.set_password("password")

        assert user.verify_password("password")
        assert not user.verify_password("mismatch")

    def test_role_assignment_missing_identifiers_raises_validation_error(
        self, user, role_assignment_missing_identifiers
    ):
        user.role_assignments = [role_assignment_missing_identifiers]

        with pytest.raises(ValidationError):
            user.save()


class TestGarden:
    v1_str = "v1"
    v2_str = "v2"
    garden_name = "test_garden"

    @classmethod
    def setup_class(cls):
        connect("beer_garden", host="mongomock://localhost")
        Garden.drop_collection()
        Garden.ensure_indexes()

    @pytest.fixture()
    def local_garden(self, mongo_conn):
        garden = Garden(name=self.garden_name, connection_type="LOCAL").save()

        yield garden

        garden.delete()

    @pytest.fixture
    def child_system(self):
        return System(name="echoer", namespace="child_garden")

    @pytest.fixture
    def child_system_v1(self, child_system):
        system: System = copy.deepcopy(child_system)
        system.version = self.v1_str
        system.save()

        yield system

        system.delete()

    @pytest.fixture
    def child_system_v2(self, child_system):
        system: System = copy.deepcopy(child_system)
        system.version = self.v2_str
        system.save()

        yield system

        system.delete()

    @pytest.fixture
    def child_system_v1_diff_id(self, child_system):
        system: System = copy.deepcopy(child_system)
        system.version = self.v1_str
        system.save()

        yield system

        system.delete()

    @pytest.fixture
    def child_garden(self, child_system_v1):
        garden = Garden(
            name="child_garden", connection_type="http", systems=[child_system_v1]
        ).save()

        yield garden

        garden.delete()

    def test_garden_names_are_required_to_be_unique(self, local_garden):
        """Attempting to create a garden that shares a name with an existing garden
        should raise an exception"""
        with pytest.raises(NotUniqueError):
            Garden(name=local_garden.name, connection_type="HTTP").save()

    def test_only_one_local_garden_may_exist(self, local_garden):
        """Attempting to create more than one garden with connection_type of LOCAL
        should raise an exception"""
        with pytest.raises(NotUniqueError):
            Garden(name=f"not{local_garden.name}", connection_type="LOCAL").save()

    def test_child_garden_system_attrib_update(self, child_garden, child_system_v2):
        """If the systems of a child garden are updated such that their names,
        namespaces, or versions are changed, the original systems are removed and
        replaced with the new systems when the garden is saved."""
        orig_system_ids = set(
            map(lambda x: str(getattr(x, "id")), child_garden.systems)  # noqa: B009
        )
        orig_system_versions = set(
            map(
                lambda x: str(getattr(x, "version")), child_garden.systems  # noqa: B009
            )
        )

        assert (
            self.v1_str in orig_system_versions
            and self.v2_str not in orig_system_versions
        )

        child_garden.systems = [child_system_v2]
        child_garden.deep_save()

        # we check that the garden written to the DB has the correct systems
        db_garden = Garden.objects().first()

        new_system_ids = set(
            map(lambda x: str(getattr(x, "id")), db_garden.systems)  # noqa: B009
        )
        new_system_versions = set(
            map(lambda x: str(getattr(x, "version")), db_garden.systems)  # noqa: B009
        )

        assert (
            self.v1_str not in new_system_versions
            and self.v2_str in new_system_versions
        )
        assert new_system_ids.intersection(orig_system_ids) == set()

    def test_child_garden_system_id_update(self, child_garden, child_system_v1_diff_id):
        """If the systems of a child garden are updated such that the names, namespaces
        and versions remain constant, but the IDs are different, the original systms
        are removed and replaced with the new systems when the garden is saved."""
        orig_system_ids = set(
            map(lambda x: str(getattr(x, "id")), child_garden.systems)  # noqa: B009
        )
        new_system_id = str(child_system_v1_diff_id.id)

        assert new_system_id not in orig_system_ids

        child_garden.systems = [child_system_v1_diff_id]
        child_garden.deep_save()
        db_garden = Garden.objects().first()

        new_system_ids = set(
            map(lambda x: str(getattr(x, "id")), db_garden.systems)  # noqa: B009
        )

        assert new_system_id in new_system_ids
        assert orig_system_ids.intersection(new_system_ids) == set()
