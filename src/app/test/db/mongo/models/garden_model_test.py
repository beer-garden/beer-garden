# -*- coding: utf-8 -*-
import copy
from contextlib import nullcontext as does_not_raise

import pytest
from mongoengine import NotUniqueError, connect
from mongoengine.errors import ValidationError

from beer_garden.db.mongo.models import Garden as MongoGarden
from beer_garden.db.mongo.models import System as MongoSystem

v1_str = "v1"
v2_str = "v2"
garden_name = "test_garden"

garbage_headers_extra_key = [
    {
        "key": "key_2",
        "value": "value_2",
        "extra_key": "value_doesnt_matter",
    },
]
garbage_headers_wrong_key = [
    {"notakey": "key_1", "value": "value_1"},
]


class TestGarden:
    @classmethod
    def setup_class(cls):
        connect("beer_garden", host="mongomock://localhost")
        MongoGarden.drop_collection()
        MongoGarden.ensure_indexes()

    @pytest.fixture()
    def local_garden(self):
        garden = MongoGarden(name=garden_name, connection_type="LOCAL").save()
        yield garden
        garden.delete()

    @pytest.fixture
    def child_system(self):
        return MongoSystem(name="echoer", namespace="child_garden")

    @pytest.fixture
    def child_system_v1(self, child_system):
        system: MongoSystem = copy.deepcopy(child_system)
        system.version = v1_str
        system.save()
        yield system
        system.delete()

    @pytest.fixture
    def child_system_v2(self, child_system):
        system: MongoSystem = copy.deepcopy(child_system)
        system.version = v2_str
        system.save()
        yield system
        system.delete()

    @pytest.fixture
    def child_system_v1_diff_id(self, child_system):
        system: MongoSystem = copy.deepcopy(child_system)
        system.version = v1_str
        system.save()
        yield system
        system.delete()

    @pytest.fixture
    def child_garden(self, child_system_v1):
        garden = MongoGarden(
            name="child_garden", connection_type="HTTP", systems=[child_system_v1]
        ).save()
        yield garden
        garden.delete()

    def test_garden_names_are_required_to_be_unique(self, local_garden):
        """Attempting to create a garden that shares a name with an existing garden
        should raise an exception"""
        with pytest.raises(NotUniqueError):
            MongoGarden(name=local_garden.name, connection_type="HTTP").save()

    def test_only_one_local_garden_may_exist(self, local_garden):
        """Attempting to create more than one garden with connection_type of LOCAL
        should raise an exception"""
        with pytest.raises(NotUniqueError):
            MongoGarden(name=f"not{local_garden.name}", connection_type="LOCAL").save()

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

        assert v1_str in orig_system_versions and v2_str not in orig_system_versions

        child_garden.systems = [child_system_v2]
        child_garden.deep_save()

        # we check that the garden written to the DB has the correct systems
        db_garden = MongoGarden.objects().first()

        new_system_ids = set(
            map(lambda x: str(getattr(x, "id")), db_garden.systems)  # noqa: B009
        )
        new_system_versions = set(
            map(lambda x: str(getattr(x, "version")), db_garden.systems)  # noqa: B009
        )

        assert v1_str not in new_system_versions and v2_str in new_system_versions
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
        db_garden = MongoGarden.objects().first()

        new_system_ids = set(
            map(lambda x: str(getattr(x, "id")), db_garden.systems)  # noqa: B009
        )

        assert new_system_id in new_system_ids
        assert orig_system_ids.intersection(new_system_ids) == set()


class TestGardenConnectionParameters:
    @classmethod
    def setup_class(cls):
        connect("beer_garden", host="mongomock://localhost")
        MongoGarden.drop_collection()
        MongoGarden.ensure_indexes()

    @pytest.fixture
    def bad_conn_params(self):
        return dict([("nonempty", "dictionaries"), ("should", "fail")])

    @pytest.fixture
    def http_conn_params(self):
        return {
            "http": {
                "port": 2337,
                "ssl": True,
                "url_prefix": "/",
                "ca_verify": True,
                "host": "bg-child1",
            }
        }

    @pytest.fixture
    def stomp_conn_params_basic(self):
        return {
            "stomp": {
                "ssl": {"use_ssl": False},
                "headers": [],
                "host": "activemq",
                "port": 61613,
                "send_destination": "send_destination",
                "subscribe_destination": "subscribe_destination",
                "username": "beer_garden",
                "password": "password",
            }
        }

    @pytest.fixture
    def stomp_conn_params_with_headers(self, stomp_conn_params_basic):
        stomp_conn_params = copy.deepcopy(stomp_conn_params_basic)
        headers = [{"key": f"key_{i+1}", "value": f"value_{i+1}"} for i in range(3)]
        stomp_conn_params["stomp"]["headers"] = headers
        return stomp_conn_params

    @pytest.fixture
    def bad_conn_params_with_partial_good(self, http_conn_params, bad_conn_params):
        return {**http_conn_params, **bad_conn_params}

    @pytest.fixture
    def bad_conn_params_with_full_good(
        self, bad_conn_params_with_partial_good, stomp_conn_params_basic
    ):
        return {**stomp_conn_params_basic, **bad_conn_params_with_partial_good}

    @pytest.mark.parametrize(
        "conn_parm",
        (
            pytest.lazy_fixture("bad_conn_params"),
            pytest.lazy_fixture("bad_conn_params_with_partial_good"),
            pytest.lazy_fixture("bad_conn_params_with_full_good"),
        ),
    )
    def test_local_garden_save_fails_with_nonempty_conn_params(self, conn_parm):
        with pytest.raises(ValidationError) as excinfo:
            MongoGarden(
                name=garden_name,
                connection_type="LOCAL",
                connection_params=conn_parm,
            ).save()
        assert "not allowed" in str(excinfo.value)

    def test_local_garden_save_succeeds_with_empty_conn_params(self):
        with does_not_raise():
            MongoGarden(
                name=garden_name, connection_type="LOCAL", connection_params={}
            ).save().delete()

    @pytest.mark.parametrize(
        "conn_parm",
        (
            pytest.lazy_fixture("bad_conn_params"),
            pytest.lazy_fixture("bad_conn_params_with_partial_good"),
            pytest.lazy_fixture("bad_conn_params_with_full_good"),
        ),
    )
    def test_remote_garden_save_fails_with_bad_conn_params(self, conn_parm):
        with pytest.raises(ValidationError) as excinfo:
            MongoGarden(
                name=garden_name,
                connection_type="HTTP",
                connection_params=conn_parm,
            ).save()
        assert "not allowed" in str(excinfo.value)

    @pytest.mark.parametrize("required", ("port", "ssl", "ca_verify", "host"))
    def test_required_http_params_missing_fails(self, http_conn_params, required):
        conn_param_values = http_conn_params["http"]
        _ = conn_param_values.pop(required)
        conn_params = {"http": conn_param_values}

        with pytest.raises(ValidationError) as excinfo:
            MongoGarden(
                name=garden_name, connection_type="HTTP", connection_params=conn_params
            ).save()
        assert "Missing data" in str(excinfo.value)

    @pytest.mark.parametrize("required", ("ssl", "host", "port"))
    def test_required_stomp_params_missing_fails(
        self, stomp_conn_params_basic, required
    ):
        conn_param_values = stomp_conn_params_basic["stomp"]
        _ = conn_param_values.pop(required)
        conn_params = {"stomp": conn_param_values}

        with pytest.raises(ValidationError) as excinfo:
            MongoGarden(
                name=garden_name, connection_type="HTTP", connection_params=conn_params
            ).save()
        assert "Missing data" in str(excinfo.value)

    def test_remote_garden_save_succeeds_with_only_good_http_headers(
        self, http_conn_params
    ):
        garden = MongoGarden(
            name=garden_name,
            connection_type="HTTP",
            connection_params=http_conn_params,
        )
        with does_not_raise():
            garden.save()
        garden.delete()

    def test_remote_garden_save_succeeds_with_only_good_stomp_headers(
        self, stomp_conn_params_with_headers
    ):
        garden = MongoGarden(
            name=garden_name,
            connection_type="STOMP",
            connection_params=stomp_conn_params_with_headers,
        )
        with does_not_raise():
            garden.save()
        garden.delete()

    @pytest.mark.parametrize(
        "bad_headers",
        (
            garbage_headers_extra_key,
            garbage_headers_wrong_key,
        ),
    )
    def test_remote_garden_save_fails_with_garbage_stomp_headers(
        self, stomp_conn_params_basic, bad_headers
    ):
        test_params = stomp_conn_params_basic["stomp"]
        test_params["headers"] = bad_headers
        connection_params = {"stomp": test_params}

        with pytest.raises(ValidationError):
            MongoGarden(
                name=garden_name,
                connection_type="STOMP",
                connection_params=connection_params,
            ).save()
