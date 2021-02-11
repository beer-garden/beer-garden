import pytest
from mock import Mock

import beer_garden
from beer_garden.api.http.authorization import PermissionRequiredAccess, Permissions
from brewtils.errors import RequestForbidden

from brewtils.models import (
    Request,
    RequestTemplate,
    System,
    Instance,
    Queue,
    Job,
    Operation,
    Principal,
    Role,
    Event,
    Permission,
)


@pytest.fixture
def get_request_mock(monkeypatch):
    mock = Mock(return_value=None)
    monkeypatch.setattr(beer_garden.api.http.filter, "get_request", mock)
    return mock


@pytest.fixture
def get_job_mock(monkeypatch):
    mock = Mock(return_value=None)
    monkeypatch.setattr(beer_garden.api.http.filter, "get_job", mock)
    return mock


@pytest.fixture
def get_system_mock(monkeypatch):
    mock = Mock(return_value=None)
    monkeypatch.setattr(beer_garden.api.http.filter, "get_system", mock)
    return mock


@pytest.fixture
def filter_brewtils_model_mock(monkeypatch):
    mock = Mock(return_value=None)
    monkeypatch.setattr(beer_garden.api.http.filter, "filter_brewtils_model", mock)
    return mock


@pytest.fixture
def get_from_kwargs_mock(monkeypatch):
    mock = Mock(return_value=(None, None))
    monkeypatch.setattr(beer_garden.api.http.filter, "_from_kwargs", mock)
    return mock


@pytest.fixture
def get_operation_db_filtering(monkeypatch):
    mock = Mock()
    monkeypatch.setattr(beer_garden.api.http.filter, "operation_db_filtering", mock)
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


def mock_principals(namespace, access_level):
    return [
        # Local Access
        (
            Principal(
                roles=[Role(permissions=[Permission(access="ADMIN", is_local=True)])]
            ),
            access_level in ["ADMIN", "OPERATOR", "READ"],
        ),
        (
            Principal(
                roles=[Role(permissions=[Permission(access="OPERATOR", is_local=True)])]
            ),
            access_level in ["OPERATOR", "READ"],
        ),
        (
            Principal(
                roles=[Role(permissions=[Permission(access="READ", is_local=True)])]
            ),
            access_level in ["READ"],
        ),
        # P Namespace Access
        (
            Principal(
                roles=[Role(permissions=[Permission(access="ADMIN", namespace="p")])]
            ),
            access_level in ["ADMIN", "OPERATOR", "READ"] and namespace == "p",
        ),
        (
            Principal(
                roles=[Role(permissions=[Permission(access="OPERATOR", namespace="p")])]
            ),
            access_level in ["OPERATOR", "READ"] and namespace == "p",
        ),
        (
            Principal(
                roles=[Role(permissions=[Permission(access="READ", namespace="p")])]
            ),
            access_level in ["READ"] and namespace == "p",
        ),
        # C Namespace Access
        (
            Principal(
                roles=[Role(permissions=[Permission(access="ADMIN", namespace="c")])]
            ),
            access_level in ["ADMIN", "OPERATOR", "READ"] and namespace == "c",
        ),
        (
            Principal(
                roles=[Role(permissions=[Permission(access="OPERATOR", namespace="c")])]
            ),
            access_level in ["OPERATOR", "READ"] and namespace == "c",
        ),
        (
            Principal(
                roles=[Role(permissions=[Permission(access="READ", namespace="c")])]
            ),
            access_level in ["READ"] and namespace == "c",
        ),
        # Mixed Access
        (
            Principal(
                roles=[
                    Role(permissions=[Permission(access="ADMIN", namespace="p")]),
                    Role(permissions=[Permission(access="READ", namespace="c")]),
                ]
            ),
            (access_level in ["ADMIN", "OPERATOR", "READ"] and namespace == "p")
            or (access_level in ["READ"] and namespace == "c"),
        ),
        (
            Principal(
                roles=[
                    Role(permissions=[Permission(access="ADMIN", namespace="c")]),
                    Role(permissions=[Permission(access="READ", namespace="p")]),
                ]
            ),
            (access_level in ["ADMIN", "OPERATOR", "READ"] and namespace == "c")
            or (access_level in ["READ"] and namespace == "p"),
        ),
    ]


def mock_functions(
    namespace, get_request_mock, get_job_mock, get_system_mock, get_from_kwargs_mock
):
    get_request_mock.return_value = Request(namespace=namespace)
    get_job_mock.return_value = Job(
        request_template=RequestTemplate(namespace=namespace)
    )
    get_system_mock.return_value = System(namespace=namespace)
    get_from_kwargs_mock.return_value = (System(namespace=namespace), None)


class TestModelFilter(object):
    @pytest.mark.parametrize(*mock_models("p"))
    def test_no_current_user(self, model):
        for access_level in ["ADMIN", "OPERATOR", "READ"]:
            with pytest.raises(RequestForbidden):
                beer_garden.api.http.filter.model_filter(
                    obj=model, required_permissions=[Permissions[access_level]]
                )

    @pytest.mark.parametrize(*mock_models("p"))
    def test_no_permissions(self, model, filter_brewtils_model_mock):
        obj = beer_garden.api.http.filter.model_filter(obj=model)
        assert obj == model
        assert not filter_brewtils_model_mock.called

    @pytest.mark.parametrize(*mock_models("p"))
    def test_admin_check(self, model, filter_brewtils_model_mock):
        principal = Principal(
            roles=[Role(permissions=[Permission(access="ADMIN", is_local=True)])]
        )

        for access_level in ["ADMIN", "OPERATOR", "READ"]:
            beer_garden.api.http.filter.model_filter(
                obj=model,
                current_user=principal,
                required_permissions=[Permissions[access_level]],
            )
            assert not filter_brewtils_model_mock.called

    @pytest.mark.parametrize(*mock_models_list("p"))
    def test_list_models(self, models, filter_brewtils_model_mock):
        principal = Principal(
            roles=[Role(permissions=[Permission(access="ADMIN", namespace="p")])]
        )
        beer_garden.api.http.filter.model_filter(
            obj=models, current_user=principal, required_permissions=[Permissions.ADMIN]
        )
        assert filter_brewtils_model_mock.call_count == len(models)


class TestFilterBrewtilsModel(object):
    @pytest.mark.parametrize(*mock_models("p"))
    @pytest.mark.parametrize("namespace", ["p"])
    @pytest.mark.parametrize("raise_error", [True, False])
    def test_p_namespace(
        self,
        get_request_mock,
        get_job_mock,
        get_system_mock,
        get_from_kwargs_mock,
        model,
        namespace,
        raise_error,
    ):

        mock_functions(
            namespace,
            get_request_mock,
            get_job_mock,
            get_system_mock,
            get_from_kwargs_mock,
        )

        for access_level in ["ADMIN", "OPERATOR", "READ"]:

            for principal, valid_access in mock_principals(namespace, access_level):

                if not valid_access and raise_error:
                    with pytest.raises(RequestForbidden):
                        beer_garden.api.http.filter.filter_brewtils_model(
                            obj=model,
                            current_user=principal,
                            required_permissions=[Permissions[access_level]],
                            raise_error=raise_error,
                        )
                else:
                    obj = beer_garden.api.http.filter.filter_brewtils_model(
                        obj=model,
                        current_user=principal,
                        required_permissions=[Permissions[access_level]],
                        raise_error=False,
                    )
                    if valid_access:
                        assert obj == model
                    else:
                        assert obj is None

    @pytest.mark.parametrize(*mock_models("c"))
    @pytest.mark.parametrize("namespace", ["c"])
    @pytest.mark.parametrize("raise_error", [True, False])
    def test_c_namespace(
        self,
        get_request_mock,
        get_job_mock,
        get_system_mock,
        get_from_kwargs_mock,
        model,
        namespace,
        raise_error,
    ):

        mock_functions(
            namespace,
            get_request_mock,
            get_job_mock,
            get_system_mock,
            get_from_kwargs_mock,
        )

        for access_level in ["ADMIN", "OPERATOR", "READ"]:

            for principal, valid_access in mock_principals(namespace, access_level):

                if not valid_access and raise_error:
                    with pytest.raises(RequestForbidden):
                        beer_garden.api.http.filter.filter_brewtils_model(
                            obj=model,
                            current_user=principal,
                            required_permissions=[Permissions[access_level]],
                            raise_error=raise_error,
                        )
                else:
                    obj = beer_garden.api.http.filter.filter_brewtils_model(
                        obj=model,
                        current_user=principal,
                        required_permissions=[Permissions[access_level]],
                        raise_error=False,
                    )
                    if valid_access:
                        assert obj == model
                    else:
                        assert obj is None

    @pytest.mark.parametrize(*mock_models("e"))
    @pytest.mark.parametrize("namespace", ["e"])
    @pytest.mark.parametrize("raise_error", [True, False])
    def test_e_namespace(
        self,
        get_request_mock,
        get_job_mock,
        get_system_mock,
        get_from_kwargs_mock,
        model,
        namespace,
        raise_error,
    ):

        mock_functions(
            namespace,
            get_request_mock,
            get_job_mock,
            get_system_mock,
            get_from_kwargs_mock,
        )

        for access_level in ["ADMIN", "OPERATOR", "READ"]:

            for principal, valid_access in mock_principals(namespace, access_level):

                if not valid_access and raise_error:
                    with pytest.raises(RequestForbidden):
                        beer_garden.api.http.filter.filter_brewtils_model(
                            obj=model,
                            current_user=principal,
                            required_permissions=[Permissions[access_level]],
                            raise_error=raise_error,
                        )
                else:
                    obj = beer_garden.api.http.filter.filter_brewtils_model(
                        obj=model,
                        current_user=principal,
                        required_permissions=[Permissions[access_level]],
                        raise_error=False,
                    )
                    if valid_access:
                        assert obj == model
                    else:

                        assert obj is None

    def test_no_schema(self):

        principal = Principal(
            roles=[Role(permissions=[Permission(access="READ", is_local=True)])]
        )
        model = {"model": False}

        # Test it is returned with proper permissions
        obj = beer_garden.api.http.filter.filter_brewtils_model(
            obj=model,
            current_user=principal,
            required_permissions=[Permissions.READ],
            raise_error=False,
        )

        assert obj == model

        # Test it is not returned without proper permissions
        obj = beer_garden.api.http.filter.filter_brewtils_model(
            obj=model,
            current_user=principal,
            required_permissions=[Permissions.ADMIN],
            raise_error=False,
        )
        assert obj is None


class TestModelDbFilter(object):
    def test_add_one_filter(self):
        one_namespace = Principal(
            roles=[Role(permissions=[Permission(access="ADMIN", namespace="p")])]
        )
        model = Operation(operation_type="REQUEST_COUNT", kwargs={})

        beer_garden.api.http.filter.model_db_filter(
            obj=model, current_user=one_namespace
        )

        assert len(model.kwargs["namespace__in"]) == 1

    def test_add_two_filters(self):
        two_namespaces = Principal(
            roles=[
                Role(
                    permissions=[
                        Permission(access="ADMIN", namespace="p"),
                        Permission(access="ADMIN", namespace="c"),
                    ]
                )
            ]
        )
        model = Operation(operation_type="REQUEST_COUNT", kwargs={})

        beer_garden.api.http.filter.model_db_filter(
            obj=model, current_user=two_namespaces
        )

        assert len(model.kwargs["namespace__in"]) == 2

    def test_add_two_filters_with_exisitng(self):
        two_namespaces = Principal(
            roles=[
                Role(
                    permissions=[
                        Permission(access="ADMIN", namespace="p"),
                        Permission(access="ADMIN", namespace="c"),
                    ]
                )
            ]
        )
        model = Operation(
            operation_type="REQUEST_COUNT", kwargs={"namespace__in": ["e"]}
        )

        beer_garden.api.http.filter.model_db_filter(
            obj=model, current_user=two_namespaces
        )

        assert len(model.kwargs["namespace__in"]) == 3

    def test_local(self, get_operation_db_filtering):
        local = Principal(
            roles=[Role(permissions=[Permission(access="ADMIN", is_local=True)])]
        )

        model = Operation(operation_type="REQUEST_COUNT", kwargs={})

        beer_garden.api.http.filter.model_db_filter(obj=model, current_user=local)

        assert not get_operation_db_filtering.called
