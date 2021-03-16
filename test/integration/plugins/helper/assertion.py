import json
import pytest

from brewtils.errors import ValidationError, SaveError


def assert_system_running(client, system_name, system_version, garden=None, **kwargs):
    system = client.find_unique_system(name=system_name, version=system_version. garden=garden)
    system_attrs = kwargs.pop('system', {})
    for key, value in system_attrs.items():
        actual = getattr(system, key)
        assert value == actual, "%s did not match. Expected (%s)\n Got: (%s)" % (key, value, actual)

    for instance in system.instances:
        assert_instance_running(instance, **kwargs)


def assert_instance_running(instance, **kwargs):
    assert instance.status == "RUNNING", \
        "status did not match. Expected (RUNNING) got (%s)" % instance.status


def assert_validation_error(testcase, client, request, **kwargs):
    assert_error_creating_request(testcase, client, request, ValidationError, **kwargs)


def assert_save_error(testcase, client, request, **kwargs):
    assert_error_creating_request(testcase, client, request, SaveError, **kwargs)

def assert_error_creating_request(testcase, client, request, exc_class, regex=None, **kwargs):
    if regex is None:
        with pytest.raises(exc_class) as ex:
            created_request = client.create_request(request)
            print("Uh-oh. Request (%s) should have errored, but didn't." % created_request.id)
    else:
        with pytest.raises(exc_class) as ex:
            created_request = client.create_request(request)
            print("Uh-oh. Request (%s) should have errored, but didn't." % created_request.id)
        ex.match(regex)

    the_exception = ex.value
    for k in kwargs.keys():
        assert getattr(the_exception, k) == kwargs[k], "Exception was thrown, but %s did " \
                                                       "not match. Expected (%s) got (%s)" % \
                                                       (k, kwargs[k], getattr(the_exception, k))


def assert_successful_request(request, **kwargs):
    assert_request(request, status='SUCCESS', **kwargs)


def assert_errored_request(request, **kwargs):
    assert_request(request, status='ERROR', **kwargs)


def assert_request(request, **kwargs):
    for (key, expected) in kwargs.items():
        actual = getattr(request, key)

        if key == "error_class" and not isinstance(expected, str):
            expected = type(expected).__name__

        if key == "output":
            try:
                assert actual == expected
            except AssertionError:
                assert json.loads(actual) == json.loads(expected), \
                    "%s did not match. Expected (%s) got (%s)" % (key, expected, actual)
        else:
            assert actual == expected, \
                "%s did not match. Expected (%s) got (%s)" % (key, expected, actual)
