from bg_utils.pika import get_routing_key, TransientPikaClient
from brewtils.models import Request
from brewtils.schema_parser import SchemaParser


class PikaClient(TransientPikaClient):
    """Pika client that exposes additional Bartender-specific operations"""

    def publish_request(self, request, **kwargs):
        kwargs['headers'] = kwargs.pop('headers', {})
        kwargs['headers'].update({'request_id': str(request.id)})
        kwargs['routing_key'] = (kwargs.pop('routing_key', None) or
                                 get_routing_key(request.system,
                                                 request.system_version,
                                                 request.instance_name))

        self.publish(SchemaParser.serialize_request(request), **kwargs)

    def start(self, system=None, version=None, instance=None, clone_id=None):
        self.publish_request(Request(system=system, system_version=version, instance_name=instance,
                                     command='_start', command_type='EPHEMERAL', parameters={}),
                             routing_key=get_routing_key(system, version, instance, clone_id,
                                                         is_admin=True))

    def stop(self, system=None, version=None, instance=None, clone_id=None):
        self.publish_request(Request(system=system, system_version=version, instance_name=instance,
                                     command='_stop', command_type='EPHEMERAL', parameters={}),
                             routing_key=get_routing_key(system, version, instance, clone_id,
                                                         is_admin=True))
