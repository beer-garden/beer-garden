from brewtils.models import Request
from brewtils.pika import TransientPikaClient
from brewtils.schema_parser import SchemaParser


def get_routing_key(*args, **kwargs):
    """Convenience method for getting the most specific routing key"""
    return get_routing_keys(*args, **kwargs)[-1]


def get_routing_keys(*args, **kwargs):
    """Get a list of routing keys for a plugin in order from least specific to most specific.

    Will return all possible routing keys to get a message to a particular system.

    args is used to specify routing words. The correct order is
       System, Version, Instance, Clone ID

    For instance:

        ['test_system'], is_admin=True:
            ['admin', 'admin.test_system']

        ['test_system', '1.0.0'], is_admin=True:
            ['admin', 'admin.test_system', 'admin.test_system.1-0-0']

        ['test_system', '1.0.0', 'default'], is_admin=True:
            ['admin', 'admin.test_system', 'admin.test_system.1-0-0',
                'admin.test_system.1-0-0.default']

        ['test_system', '1.0.0', 'default', 'random_text'], is_admin=True:
            ['admin', 'admin.test_system', 'admin.test_system.1-0-0',
                'admin.test_system.1-0-0.default', 'admin.test_system.1-0-0.default.random_text']

    NOTE: Because RabbitMQ uses '.' as the word delimiter all '.' in routing words will be
        replaced with '-'

    :param args: List of routing key words to include in the routing keys
    :param kwargs: is_admin: Will prepend 'admin' to all generated keys if True
    :return: List of routing keys, ordered from general to specific
    """
    routing_keys = ["admin"] if kwargs.get("is_admin", False) else []

    for arg in (y for y in args if y is not None):
        # Make sure we don't have any extra word delimiters
        new_key = arg.replace(".", "-")

        routing_keys.append(
            routing_keys[-1] + "." + new_key if len(routing_keys) else new_key
        )

    return routing_keys


class PikaClient(TransientPikaClient):
    """Pika client that exposes additional Bartender-specific operations"""

    def publish_request(self, request, **kwargs):
        if "headers" not in kwargs:
            kwargs["headers"] = {}
        kwargs["headers"]["request_id"] = str(request.id)

        if "routing_key" not in kwargs:
            kwargs["routing_key"] = get_routing_key(
                request.system, request.system_version, request.instance_name
            )

        return self.publish(SchemaParser.serialize_request(request), **kwargs)

    def start(self, system=None, version=None, instance=None, clone_id=None):
        self.publish_request(
            Request(
                system=system,
                system_version=version,
                instance_name=instance,
                command="_start",
                command_type="EPHEMERAL",
                parameters={},
            ),
            routing_key=get_routing_key(
                system, version, instance, clone_id, is_admin=True
            ),
        )

    def stop(self, system=None, version=None, instance=None, clone_id=None):
        self.publish_request(
            Request(
                system=system,
                system_version=version,
                instance_name=instance,
                command="_stop",
                command_type="EPHEMERAL",
                parameters={},
            ),
            routing_key=get_routing_key(
                system, version, instance, clone_id, is_admin=True
            ),
        )
