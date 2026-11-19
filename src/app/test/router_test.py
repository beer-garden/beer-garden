# -*- coding: utf-8 -*-
import pytest
from brewtils.models import Connection
from brewtils.models import Garden as BrewtilsGarden
from brewtils.models import Instance as BrewtilsInstance
from brewtils.models import Operation
from brewtils.models import Request as BrewtilsRequest
from brewtils.models import System as BrewtilsSystem
from brewtils.schema_parser import SchemaParser
from mock import Mock

import beer_garden.garden
import beer_garden.router
from beer_garden.db.mongo.models import Garden, Request, System
from beer_garden.errors import UnknownGardenException
from beer_garden.garden import create_garden
from beer_garden.router import _determine_target
from beer_garden.systems import create_system


@pytest.fixture
def op():
    return Operation(source_garden_name="parent")


class TestDetermineTarget:
    def test_neither(self, monkeypatch, op):
        monkeypatch.setattr(
            beer_garden.router, "_target_from_type", Mock(return_value=None)
        )
        with pytest.raises(UnknownGardenException):
            _determine_target(op)

    def test_target_from_op(self, monkeypatch, op):
        monkeypatch.setattr(
            beer_garden.router, "_target_from_type", Mock(return_value=None)
        )
        monkeypatch.setattr(
            beer_garden.router, "get_garden", Mock(return_value=Garden(name="parent"))
        )
        op.target_garden_name = "parent"

        assert _determine_target(op) == "parent"

    def test_target_from_type(self, monkeypatch, op):
        monkeypatch.setattr(
            beer_garden.router, "_target_from_type", Mock(return_value="parent")
        )

        assert _determine_target(op) == "parent"

    def test_same(self, monkeypatch, op):
        monkeypatch.setattr(
            beer_garden.router, "_target_from_type", Mock(return_value="child")
        )
        op.target_garden_name = "child"

        assert _determine_target(op) == "child"

    def test_provided(self, monkeypatch, op):
        monkeypatch.setattr(
            beer_garden.router, "_target_from_type", Mock(return_value="child")
        )
        monkeypatch.setattr(
            beer_garden.router, "get_garden", Mock(return_value=Garden(name="parent"))
        )
        op.target_garden_name = "parent"

        assert _determine_target(op) == "parent"


class TestRequestRouting:

    @pytest.fixture(autouse=True)
    def drop(self):
        yield
        Garden.drop_collection()
        System.drop_collection()
        Request.drop_collection()

    @pytest.fixture
    def localgarden_system(self):
        yield create_system(
            BrewtilsSystem(
                name="localsystem",
                version="1.2.3",
                namespace="somegarden",
                local=True,
                instances=[BrewtilsInstance(name="default", status="RUNNING")],
            )
        )

    @pytest.fixture
    def localgarden(self, localgarden_system):
        yield create_garden(
            BrewtilsGarden(
                name="somegarden",
                connection_type="LOCAL",
                systems=[localgarden_system],
                version=beer_garden.__version__,
            )
        )

    @pytest.fixture
    def remotegarden(self):
        one_hop = create_garden(
            BrewtilsGarden(
                name="one_hop",
                connection_type="REMOTE",
                publishing_connections=[Connection(api="HTTP", status="RECEIVING")],
                systems=[
                    BrewtilsSystem(
                        name="one_hop_system",
                        version="1.2.3",
                        namespace="one_hop_garden",
                        local=False,
                        instances=[BrewtilsInstance(name="default", status="RUNNING")],
                    )
                ],
                version="1.0.0",
            )
        )

        two_hop_garden = create_garden(
            BrewtilsGarden(
                name="two_hop",
                connection_type="REMOTE",
                publishing_connections=[Connection(api="HTTP", status="RECEIVING")],
                parent="one_hop",
                has_parent=True,
                systems=[
                    BrewtilsSystem(
                        name="two_hop_system",
                        version="1.2.3",
                        namespace="two_hop_garden",
                        local=False,
                        instances=[BrewtilsInstance(name="default", status="RUNNING")],
                    )
                ],
                version="1.0.0",
            )
        )

        one_hop.children = [two_hop_garden]
        yield one_hop

    def test_cached_routes(self, localgarden, remotegarden):
        beer_garden.router.system_id_routes = {}
        beer_garden.router.instance_id_routes = {}
        beer_garden.router.system_name_routes = {}

        beer_garden.router.setup_routing()
        assert len(beer_garden.router.system_id_routes) == 3
        assert len(beer_garden.router.instance_id_routes) == 3
        assert len(beer_garden.router.system_name_routes) == 3

        for system in remotegarden.systems:
            assert beer_garden.router.system_id_routes[system.id] == "one_hop"
            assert beer_garden.router.system_name_routes[str(system)] == "one_hop"
            for instance in system.instances:
                assert beer_garden.router.instance_id_routes[instance.id] == "one_hop"

        for system in localgarden.systems:
            assert beer_garden.router.system_id_routes[system.id] == "somegarden"
            assert beer_garden.router.system_name_routes[str(system)] == "somegarden"
            for instance in system.instances:
                assert (
                    beer_garden.router.instance_id_routes[instance.id] == "somegarden"
                )

        for system in remotegarden.children[0].systems:
            assert beer_garden.router.system_id_routes[system.id] == "two_hop"
            assert beer_garden.router.system_name_routes[str(system)] == "two_hop"
            for instance in system.instances:
                assert beer_garden.router.instance_id_routes[instance.id] == "two_hop"

    def test_request_routing_one_hop(self, localgarden, remotegarden):
        beer_garden.router.setup_routing()
        operation = Operation(
            operation_type="REQUEST_CREATE",
            model=BrewtilsRequest(
                system="one_hop_system",
                system_version="1.2.3",
                namespace="one_hop_garden",
            ),
            model_type="Request",
        )

        target_garden = beer_garden.router._target_from_type(operation)
        assert target_garden == "one_hop"
        routing_garden = beer_garden.router.determine_route_garden(target_garden)
        assert routing_garden.name == "one_hop"

    def test_request_routing_two_hop(self, localgarden, remotegarden):
        beer_garden.router.setup_routing()
        operation = Operation(
            operation_type="REQUEST_CREATE",
            model=BrewtilsRequest(
                system="two_hop_system",
                system_version="1.2.3",
                namespace="two_hop_garden",
            ),
            model_type="Request",
        )

        target_garden = beer_garden.router._target_from_type(operation)
        assert target_garden == "two_hop"
        routing_garden = beer_garden.router.determine_route_garden(target_garden)
        assert routing_garden.name == "one_hop"

    def test_forward_request(self, monkeypatch, localgarden, remotegarden):

        beer_garden.router.setup_routing()
        forward_mock = Mock()
        monkeypatch.setattr(beer_garden.router, "_forward_http", forward_mock)
        monkeypatch.setattr(
            beer_garden.router.asyncio, "get_event_loop", Mock(return_value=None)
        )

        operation = Operation(
            operation_type="REQUEST_CREATE",
            model=BrewtilsRequest(
                system="two_hop_system",
                system_version="1.2.3",
                namespace="two_hop_garden",
                instance_name="default",
                command="test",
            ),
            model_type="Request",
        )

        beer_garden.router.route(operation)

        assert forward_mock.call_count == 1
        assert forward_mock.call_args[0][0].target_garden_name == "two_hop"
        assert forward_mock.call_args[0][1].name == "one_hop"

    def test_forward_request_provided(self, monkeypatch, localgarden, remotegarden):

        beer_garden.router.setup_routing()
        forward_mock = Mock()
        target_from_type_mock = Mock()
        monkeypatch.setattr(beer_garden.router, "_forward_http", forward_mock)
        monkeypatch.setattr(
            beer_garden.router, "_target_from_type", target_from_type_mock
        )

        monkeypatch.setattr(
            beer_garden.router.asyncio, "get_event_loop", Mock(return_value=None)
        )

        operation = Operation(
            operation_type="REQUEST_CREATE",
            model=BrewtilsRequest(
                system="two_hop_system",
                system_version="1.2.3",
                namespace="two_hop_garden",
                instance_name="default",
                command="test",
            ),
            target_garden_name="two_hop",
            model_type="Request",
        )

        beer_garden.router.route(operation)

        assert forward_mock.call_count == 1
        assert target_from_type_mock.call_count == 0
        assert forward_mock.call_args[0][0].target_garden_name == "two_hop"
        assert forward_mock.call_args[0][1].name == "one_hop"

    def test_process_garden_operation(self, monkeypatch, localgarden):

        def mock_request(request):
            return request

        beer_garden.router.setup_routing()
        garden_sync_mock = Mock()

        monkeypatch.setattr(beer_garden.router, "execute_local", garden_sync_mock)
        monkeypatch.setattr(beer_garden.router, "create_request", mock_request)
        monkeypatch.setattr(beer_garden.router, "update_request", mock_request)

        monkeypatch.setattr(
            beer_garden.router.asyncio, "get_event_loop", Mock(return_value=None)
        )

        target_operation = Operation(
            operation_type="GARDEN_SYNC",
        )

        operation = Operation(
            operation_type="REQUEST_CREATE",
            model=BrewtilsRequest(
                command_type="GARDEN",
                parameters={
                    "operation": SchemaParser.serialize_operation(
                        target_operation, to_string=False
                    )
                },
            ),
            model_type="Request",
        )

        result = beer_garden.router.route(operation)

        assert garden_sync_mock.call_count == 1
        args, _ = garden_sync_mock.call_args
        assert args[0].operation_type == "GARDEN_SYNC"
        assert args[0].source_garden_name == localgarden.name
        assert args[0].target_garden_name == localgarden.name

        assert result.status == "SUCCESS"

    def test_process_garden_operation_exception(self, monkeypatch, localgarden):

        def mock_request(request):
            return request

        beer_garden.router.setup_routing()
        garden_sync_mock = Mock(side_effect=Exception("Raised Exception"))

        monkeypatch.setattr(beer_garden.router, "execute_local", garden_sync_mock)
        monkeypatch.setattr(beer_garden.router, "create_request", mock_request)
        monkeypatch.setattr(beer_garden.router, "update_request", mock_request)

        monkeypatch.setattr(
            beer_garden.router.asyncio, "get_event_loop", Mock(return_value=None)
        )

        target_operation = Operation(
            operation_type="GARDEN_SYNC",
        )

        operation = Operation(
            operation_type="REQUEST_CREATE",
            model=BrewtilsRequest(
                command_type="GARDEN",
                parameters={
                    "operation": SchemaParser.serialize_operation(
                        target_operation, to_string=False
                    )
                },
            ),
            model_type="Request",
        )

        result = beer_garden.router.route(operation)

        assert garden_sync_mock.call_count == 1
        args, _ = garden_sync_mock.call_args
        assert args[0].operation_type == "GARDEN_SYNC"
        assert args[0].source_garden_name == localgarden.name
        assert args[0].target_garden_name == localgarden.name

        assert result.status == "ERROR"
        assert result.output == "Raised Exception"
        assert result.error_class == "Exception"
