import copy
import json
from contextlib import nullcontext as does_not_raise

import pytest
from marshmallow.exceptions import ValidationError as MarshmallowValidationError

from beer_garden.api.http.schemas.v1.garden import GardenConnectionsParamsSchema

garbage_headers_example_1 = [
    {"headers": {"0": {"0": {"": {"key": "key_1", "value": "value_1"}}}}},
]
garbage_headers_example_2 = [
    {"key": "key_1", "value": "value_1"},
    {"key": "key_2", "value": "value_2"},
    {
        "key": "key_3",
        "value": "value_3",
        "headers": {
            "3": {"3": {"": {"key": "key_different", "value": "value_different"}}}
        },
    },
]
garbage_headers_example_3 = [
    {"key": "key_1", "value": "value_1"},
    {"key": "key_2", "value": "value_2"},
    {
        "key": "key_3",
        "value": "value_3",
        "headers": {
            "3": {"3": {"": {"key": "key_different", "value": "value_different"}}}
        },
    },
    {"headers": {"2": {"2": {"": {"key": "key4", "value": "value4"}}}}},
]


class TestGardenSchema:
    @pytest.fixture
    def bad_conn_params(self):
        return dict([("nonempty", "dictionaries"), ("should", "fail")])

    @pytest.fixture
    def http_good_conn_params(self):
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
    def stomp_good_conn_params_basic(self):
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
    def stomp_good_conn_params_with_headers(self, stomp_good_conn_params_basic):
        stomp_conn_params = copy.deepcopy(stomp_good_conn_params_basic)
        headers = [{"key": f"key_{i+1}", "value": f"value_{i+1}"} for i in range(3)]
        stomp_conn_params["stomp"]["headers"] = headers
        return stomp_conn_params

    @pytest.fixture
    def full_good_conn_params(
        self, http_good_conn_params, stomp_good_conn_params_with_headers
    ):
        return {**http_good_conn_params, **stomp_good_conn_params_with_headers}

    @pytest.fixture
    def bad_conn_params_with_partial_good(self, http_good_conn_params, bad_conn_params):
        return {**http_good_conn_params, **bad_conn_params}

    @pytest.fixture
    def bad_conn_params_with_full_good(
        self, bad_conn_params_with_partial_good, stomp_good_conn_params_basic
    ):
        return {**stomp_good_conn_params_basic, **bad_conn_params_with_partial_good}

    @pytest.mark.parametrize(
        "conn_params",
        (
            pytest.lazy_fixture("bad_conn_params"),
            pytest.lazy_fixture(
                "bad_conn_params_with_partial_good",
            ),
            pytest.lazy_fixture("bad_conn_params_with_full_good"),
        ),
    )
    def test_load_and_dump_fail_on_extra_keys(self, conn_params):
        with pytest.raises(MarshmallowValidationError):
            GardenConnectionsParamsSchema().load(conn_params)
        with pytest.raises(MarshmallowValidationError):
            GardenConnectionsParamsSchema().loads(json.dumps(conn_params))
        with pytest.raises(MarshmallowValidationError):
            GardenConnectionsParamsSchema().dump(conn_params)
        with pytest.raises(MarshmallowValidationError):
            GardenConnectionsParamsSchema().dumps(conn_params)

    @pytest.mark.parametrize("required", ("port", "ssl", "ca_verify", "host"))
    def test_http_fails_with_missing_params(self, http_good_conn_params, required):
        params = http_good_conn_params["http"]
        params.pop(required)
        bad_conn_params = {"http": params}

        with pytest.raises(MarshmallowValidationError):
            GardenConnectionsParamsSchema().load(bad_conn_params)
        with pytest.raises(MarshmallowValidationError):
            GardenConnectionsParamsSchema().loads(json.dumps(bad_conn_params))
        with pytest.raises(MarshmallowValidationError):
            GardenConnectionsParamsSchema().dump(bad_conn_params)
        with pytest.raises(MarshmallowValidationError):
            GardenConnectionsParamsSchema().dumps(bad_conn_params)

    @pytest.mark.parametrize("required", ("ssl", "host", "port"))
    def test_stomp_fails_with_missing_params(
        self, stomp_good_conn_params_basic, required
    ):
        params = stomp_good_conn_params_basic["stomp"]
        params.pop(required)
        bad_conn_params = {"stomp": params}

        with pytest.raises(MarshmallowValidationError):
            GardenConnectionsParamsSchema().load(bad_conn_params)
        with pytest.raises(MarshmallowValidationError):
            GardenConnectionsParamsSchema().loads(json.dumps(bad_conn_params))
        with pytest.raises(MarshmallowValidationError):
            GardenConnectionsParamsSchema().dump(bad_conn_params)
        with pytest.raises(MarshmallowValidationError):
            GardenConnectionsParamsSchema().dumps(bad_conn_params)

    @pytest.mark.parametrize(
        "bad_headers",
        (
            garbage_headers_example_1,
            garbage_headers_example_2,
            garbage_headers_example_3,
        ),
    )
    def test_stomp_fails_with_garbage_header_params(
        self, stomp_good_conn_params_basic, bad_headers
    ):
        test_params = stomp_good_conn_params_basic["stomp"]
        test_params["headers"] = bad_headers

        with pytest.raises(MarshmallowValidationError):
            GardenConnectionsParamsSchema().load({"stomp": test_params})
        with pytest.raises(MarshmallowValidationError):
            GardenConnectionsParamsSchema().loads(json.dumps({"stomp": test_params}))
        with pytest.raises(MarshmallowValidationError):
            GardenConnectionsParamsSchema().dump({"stomp": test_params})
        with pytest.raises(MarshmallowValidationError):
            GardenConnectionsParamsSchema().dumps({"stomp": test_params})

    def test_good_params_successful(self, full_good_conn_params):
        with does_not_raise():
            _ = GardenConnectionsParamsSchema().load(full_good_conn_params)
            _ = GardenConnectionsParamsSchema().loads(json.dumps(full_good_conn_params))
            _ = GardenConnectionsParamsSchema().dump(full_good_conn_params)
            _ = GardenConnectionsParamsSchema().dumps(full_good_conn_params)
