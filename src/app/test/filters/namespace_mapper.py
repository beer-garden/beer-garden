import pytest
from mock import Mock

import beer_garden.filters.garden_namespace_mapper

from brewtils.models import (
    Request,
    RequestTemplate,
    System,
    Instance,
    Queue,
    Job,
    Operation,
    Event,
)


@pytest.fixture
def get_request_mock(monkeypatch):
    mock = Mock(return_value=None)
    monkeypatch.setattr(beer_garden.filters.garden_namespace_mapper, "get_request", mock)
    return mock


@pytest.fixture
def get_job_mock(monkeypatch):
    mock = Mock(return_value=None)
    monkeypatch.setattr(beer_garden.filters.garden_namespace_mapper, "get_job", mock)
    return mock


@pytest.fixture
def get_system_mock(monkeypatch):
    mock = Mock(return_value=None)
    monkeypatch.setattr(beer_garden.filters.garden_namespace_mapper, "get_system", mock)
    return mock


@pytest.fixture
def get_from_kwargs_mock(monkeypatch):
    mock = Mock(return_value=(None, None))
    monkeypatch.setattr(beer_garden.filters.garden_namespace_mapper, "_from_kwargs", mock)
    return mock


def mock_models(namespace):
    return (
        "model",
        [
            Instance(),
            Job(request_template=RequestTemplate(namespace=namespace)),
            Request(namespace=namespace),
            RequestTemplate(namespace=namespace),
            System(namespace=namespace),
            Queue(system_id=namespace),
            Operation(operation_type="REQUEST", kwargs={"request_id": namespace}),
            Operation(operation_type="SYSTEM", kwargs={"system_id": namespace}),
            Operation(operation_type="INSTANCE", kwargs={"instance_id": namespace}),
            Operation(operation_type="JOB", kwargs={"job_id": namespace}),
            Operation(operation_type="INSTANCE", model=Instance()),
            Operation(
                operation_type="JOB",
                model=Job(request_template=RequestTemplate(namespace=namespace)),
            ),
            Operation(operation_type="REQUEST", model=Request(namespace=namespace)),
            Operation(
                operation_type="REQUEST", model=RequestTemplate(namespace=namespace)
            ),
            Operation(operation_type="SYSTEM", model=System(namespace=namespace)),
            Event(payload=Instance()),
            Event(payload=Job(request_template=RequestTemplate(namespace=namespace))),
            Event(payload=Request(namespace=namespace)),
            Event(payload=RequestTemplate(namespace=namespace)),
            Event(payload=System(namespace=namespace)),
        ],
    )


def mock_models_list(namespace):
    return (
        "models",
        [
            [
                Instance(),
                Job(request_template=RequestTemplate(namespace=namespace)),
                Request(namespace=namespace),
                RequestTemplate(namespace=namespace),
                System(namespace=namespace),
                Queue(system_id=namespace),
            ]
        ],
    )


def mock_functions(
    namespace, get_request_mock, get_job_mock, get_system_mock, get_from_kwargs_mock
):
    get_request_mock.return_value = Request(namespace=namespace)
    get_job_mock.return_value = Job(
        request_template=RequestTemplate(namespace=namespace)
    )
    get_system_mock.return_value = System(namespace=namespace)
    get_from_kwargs_mock.return_value = (System(namespace=namespace), None)


class TestFindNamespace(object):
    @pytest.mark.parametrize(*mock_models("p"))
    @pytest.mark.parametrize("namespace", ["p"])
    def test_p_namespace(
        self,
        get_request_mock,
        get_job_mock,
        get_system_mock,
        get_from_kwargs_mock,
        model,
        namespace,
    ):
        mock_functions(
            namespace,
            get_request_mock,
            get_job_mock,
            get_system_mock,
            get_from_kwargs_mock,
        )

        assert (
                beer_garden.filters.garden_namespace_mapper.find_obj_garden_namespace(model) == namespace
        )
