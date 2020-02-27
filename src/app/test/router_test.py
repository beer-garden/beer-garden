# -*- coding: utf-8 -*-
import pytest
from mock import Mock

import beer_garden
import beer_garden.commands
import beer_garden.instances
import beer_garden.scheduler
import beer_garden.requests
import beer_garden.systems
import beer_garden.log
import beer_garden.queues
import beer_garden.garden
import beer_garden.plugin

from brewtils.schema_parser import SchemaParser

from beer_garden.errors import RoutingRequestException

import beer_garden.router as router


def _mock_local_garden(monkeypatch, return_value="default"):
    process_mock = Mock()
    process_mock.return_value = return_value
    monkeypatch.setattr(router, "_local_garden", process_mock)


def _mock_internal_routing(monkeypatch, route_class):
    process_mock = Mock()
    process_mock.return_value = route_class == "commands"
    monkeypatch.setattr(beer_garden.commands, "route_request", process_mock)

    process_mock = Mock()
    process_mock.return_value = route_class == "instances"
    monkeypatch.setattr(beer_garden.instances, "route_request", process_mock)

    process_mock = Mock()
    process_mock.return_value = route_class == "instances"
    monkeypatch.setattr(beer_garden.plugin, "route_request", process_mock)

    process_mock = Mock()
    process_mock.return_value = route_class == "jobs"
    monkeypatch.setattr(beer_garden.scheduler, "route_request", process_mock)

    process_mock = Mock()
    process_mock.return_value = route_class == "requests"
    monkeypatch.setattr(beer_garden.requests, "route_request", process_mock)

    process_mock = Mock()
    process_mock.return_value = route_class == "systems"
    monkeypatch.setattr(beer_garden.systems, "route_request", process_mock)

    process_mock = Mock()
    process_mock.return_value = route_class == "logs"
    monkeypatch.setattr(beer_garden.log, "route_request", process_mock)

    process_mock = Mock()
    process_mock.return_value = route_class == "queues"
    monkeypatch.setattr(beer_garden.queues, "route_request", process_mock)


def _mock_instance_lookup(monkeypatch):
    instance_mock = Mock()
    instance_mock.return_value = {}
    monkeypatch.setattr(beer_garden.instances, "get_instance", instance_mock)


class mock_system_obj:
    def __init__(self, id=123):
        self.id = id
        self.namespace = "namespace"
        self.name = "system"
        self.version = "version"

    def __str__(self):
        return "%s:%s-%s" % (self.namespace, self.name, self.version)


def _mock_system_lookup(monkeypatch, id=123):
    system_mock = Mock()

    system_mock.return_value = mock_system_obj(id=id)
    monkeypatch.setattr(beer_garden.systems, "get_system", system_mock)


def _mock_systems_lookup(monkeypatch, id=123):
    systems_mock = Mock()

    systems_mock.return_value = [mock_system_obj(id=id)]
    monkeypatch.setattr(beer_garden.systems, "get_systems", systems_mock)


def _mock_forward(monkeypatch, response=True):
    forward_mock = Mock()
    forward_mock.return_value = response
    monkeypatch.setattr(router, "forward_routing", forward_mock)


class mock_request:
    def __init__(self, namespace="namespace", system="system", version="version"):
        self.namespace = namespace
        self.system = system
        self.version = version
        self.schema = "RequestTemplateSchema"


def _mock_get_request(monkeypatch):
    request_mock = Mock()

    request_mock.return_value = mock_request()
    monkeypatch.setattr(beer_garden.requests, "get_request", request_mock)


def _mock_schema_parse_request(
    monkeypatch, namespace="namespace", system="system", version="version"
):
    schema_mock = Mock()
    schema_mock.return_value = mock_request(
        namespace=namespace, system=system, version=version
    )
    monkeypatch.setattr(SchemaParser, "parse_request", schema_mock)


def _mock_schema_parse_system(monkeypatch, garden_name="default"):
    schema_mock = Mock()
    schema_mock.return_value = mock_system_obj(garden_name)
    monkeypatch.setattr(SchemaParser, "parse_system", schema_mock)


class mock_garden_router:
    def __init__(self, connection_type="HTTP", garden_name="default"):
        self.connection_type = connection_type
        self.garden_name = garden_name


def _mock_get_garden(monkeypatch, garden=None):
    garden_mock = Mock()
    garden_mock.return_value = garden or mock_garden_router()
    monkeypatch.setattr(beer_garden.garden, "get_garden", garden_mock)


def _mock_forward_http(monkeypatch, response=True):
    forward_http_mock = Mock()
    forward_http_mock.return_value = response
    monkeypatch.setattr(router, "forward_routing_http", forward_http_mock)


def _mock_create_system_mapping(
    system=None, garden_name="default", mapped_garden_name="default"
):
    router.update_garden_connection(mock_garden_router(garden_name=garden_name))
    router.update_system_mapping(system or mock_system_obj(), mapped_garden_name)


@pytest.mark.skip(reason="Skipping until structure is settled")
class TestRouter(object):
    def test_no_route_class(self, monkeypatch):
        _mock_local_garden(monkeypatch)
        with pytest.raises(RoutingRequestException) as e:
            router.route_request(route_class=None)
        assert str(e.value) == "Unable to identify route"

    def test_no_obj_id_delete(self, monkeypatch):
        _mock_local_garden(monkeypatch)

        for route_class in router.Routing_Eligible:
            with pytest.raises(RoutingRequestException) as e:
                router.route_request(
                    route_class=route_class,
                    route_type=router.Route_Type.DELETE,
                    src_garden_name="anything",
                )
            assert (
                str(e.value)
                == "Unable to lookup %s for Route delete because ID was not provided"
                % route_class
            )

    def test_bad_route_class(self, monkeypatch):
        _mock_local_garden(monkeypatch)
        bad_route_class = "ABC"
        with pytest.raises(RoutingRequestException) as e:
            router.route_request(route_class=bad_route_class)
        assert str(e.value) == "No route for %s exist" % bad_route_class

    def test_generate_route_class(self, monkeypatch):
        _mock_local_garden(monkeypatch)
        _mock_internal_routing(monkeypatch, "requests")

        assert router.route_request(brewtils_obj=mock_request()) is True

    def test_job_routing(self, monkeypatch):
        _mock_local_garden(monkeypatch)
        _mock_internal_routing(monkeypatch, "jobs")
        assert router.route_request(route_class=router.Route_Class.JOB) is True

    def test_log_routing(self, monkeypatch):
        _mock_local_garden(monkeypatch)
        _mock_internal_routing(monkeypatch, "logs")
        assert router.route_request(route_class=router.Route_Class.LOGGING) is True

    def test_queues_routing(self, monkeypatch):
        _mock_local_garden(monkeypatch)
        _mock_internal_routing(monkeypatch, "queues")
        assert router.route_request(route_class=router.Route_Class.QUEUE) is True

    def test_instance_forward(self, monkeypatch):
        _mock_local_garden(monkeypatch)

        # Test forwarding Request to Child
        _mock_instance_lookup(monkeypatch)

        _mock_forward(monkeypatch)
        _mock_internal_routing(monkeypatch, "fail-all")
        _mock_systems_lookup(monkeypatch)
        _mock_create_system_mapping(
            garden_name="default2", mapped_garden_name="default2"
        )

        assert (
            router.route_request(
                route_class=router.Route_Class.INSTANCE,
                route_type=router.Route_Type.DELETE,
                obj_id="abc",
            )
            is True
        )

        router.remove_system_mapping(mock_system_obj())

        # Test routing request internally
        _mock_internal_routing(monkeypatch, "instances")
        _mock_forward(monkeypatch, response=False)
        assert router.route_request(route_class=router.Route_Class.INSTANCE) is True

        # Test routing request internally
        _mock_instance_lookup(monkeypatch)
        _mock_systems_lookup(monkeypatch)
        _mock_forward(monkeypatch, response=False)
        _mock_create_system_mapping()

        assert (
            router.route_request(
                route_class=router.Route_Class.INSTANCE,
                route_type=router.Route_Type.DELETE,
                obj_id="abc",
            )
            is True
        )

    def test_request_forward(self, monkeypatch):
        _mock_local_garden(monkeypatch)

        # Test forwarding Request to Child
        _mock_get_request(monkeypatch)
        _mock_systems_lookup(monkeypatch)
        _mock_create_system_mapping(
            garden_name="default2", mapped_garden_name="default2"
        )
        _mock_forward(monkeypatch)
        _mock_internal_routing(monkeypatch, "fail-all")

        # Test Create Forwarding
        _mock_schema_parse_request(monkeypatch)
        assert (
            router.route_request(
                route_class=router.Route_Class.REQUEST,
                route_type=router.Route_Type.CREATE,
                brewtils_obj="{}",
            )
            is True
        )

        router.remove_system_mapping(mock_system_obj())

        # Test routing request internally
        _mock_internal_routing(monkeypatch, "requests")
        _mock_forward(monkeypatch, response=False)
        assert router.route_request(route_class=router.Route_Class.REQUEST) is True

        # Test routing request internally
        _mock_get_request(monkeypatch)
        _mock_systems_lookup(monkeypatch)
        _mock_forward(monkeypatch, response=False)
        assert (
            router.route_request(
                route_class=router.Route_Class.REQUEST,
                route_type=router.Route_Type.DELETE,
                obj_id="abc",
            )
            is True
        )

    def test_system_forward(self, monkeypatch):
        _mock_local_garden(monkeypatch)

        # Test forwarding Request to Child
        _mock_system_lookup(monkeypatch)
        _mock_forward(monkeypatch)
        _mock_internal_routing(monkeypatch, "fail-all")
        _mock_create_system_mapping(
            garden_name="default2", mapped_garden_name="default2"
        )

        assert (
            router.route_request(
                route_class=router.Route_Class.SYSTEM,
                route_type=router.Route_Type.DELETE,
                obj_id="abc",
            )
            is True
        )

        print(router.System_Garden_Mapping)
        router.remove_system_mapping(mock_system_obj())
        print(router.System_Garden_Mapping)

        # Test routing request internally
        _mock_internal_routing(monkeypatch, "systems")
        _mock_forward(monkeypatch, response=False)
        assert router.route_request(route_class=router.Route_Class.SYSTEM) is True

        # Test routing request internally
        # _mock_get_request(monkeypatch)
        # _mock_system_lookup(monkeypatch)
        _mock_forward(monkeypatch, response="Foo")

        assert (
            router.route_request(
                route_class=router.Route_Class.SYSTEM,
                route_type=router.Route_Type.DELETE,
                obj_id="abc",
            )
            is True
        )

    def test_forward_routing(self, monkeypatch):
        garden = mock_garden_router(connection_type="HTTP")
        _mock_forward_http(monkeypatch, response=True)
        _mock_get_garden(monkeypatch, garden)
        router.update_garden_connection(garden)

        assert router.forward_routing(garden_name="default")
        router.remove_garden_connection(garden)

        bad_connection_type = "SSL"
        garden = mock_garden_router(connection_type=bad_connection_type)
        router.update_garden_connection(garden)
        with pytest.raises(RoutingRequestException) as e:
            _mock_get_garden(monkeypatch, garden)
            router.forward_routing(garden_name="default")
        assert str(e.value) == "No forwarding route for %s exist" % bad_connection_type
