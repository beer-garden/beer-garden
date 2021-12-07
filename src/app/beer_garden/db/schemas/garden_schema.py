import logging

from brewtils.models import Garden as BrewtilsGarden
from brewtils.schemas import StatusInfoSchema  # noqa # until we can fully decouple
from brewtils.schemas import SystemSchema  # noqa # until we can fully decouple
from marshmallow import Schema, ValidationError, fields
from marshmallow.decorators import post_load, pre_dump, pre_load, validates_schema
from mongoengine.queryset.queryset import QuerySet

logger = logging.getLogger(__name__)


class GardenBaseSchema(Schema):
    """Class to give Marshmallow Schemas the desired behavior of throwing
    exceptions on errors when marshalling/unmarshalling. Otherwise, each line of code
    utilizing these would need to pull apart MarshalResult objects in order to return
    a meaningful error."""

    @validates_schema(skip_on_field_errors=False)
    def validate_all_keys(self, data, **kwargs):
        # do not allow extraneous keys if working on a dictionary
        if isinstance(data, dict):
            extra_args = [key for key in data.keys() if key not in self.fields]

            if len(extra_args) > 0:
                raise ValidationError(
                    f"Only {', '.join(self.fields.keys())} allowed as keys; "
                    f"these are not allowed: {', '.join(extra_args)}"
                )

    # def load(self, data, many=None, partial=None):
    #     logger.error("In load")
    #     return super().load(data, many=many, partial=partial)

    def dump(self, obj, many=None, update_fields=True, **kwargs):
        if isinstance(obj, (list, QuerySet)):
            many = True

        return super().dump(obj, many=many, update_fields=update_fields, **kwargs)


def _port_validator(value):
    return 0 < value < 65535


class HttpConnectionParamsSchema(GardenBaseSchema):
    host = fields.String(required=True)
    port = fields.Integer(
        required=True,
        validate=_port_validator,
        error_messages={
            **fields.Field.default_error_messages,
            **{"validator_failed": "Value out of range for ports"},
        },
    )
    url_prefix = fields.String(required=True, dump_default="/", load_default="/")
    ca_cert = fields.String(required=False, allow_none=True)
    ca_verify = fields.Boolean(required=True)
    client_cert = fields.String(required=False, allow_none=True)
    client_key = fields.String(required=False, allow_none=True)
    ssl = fields.Boolean(required=True)


class StompSSLParamsSchema(GardenBaseSchema):
    use_ssl = fields.Boolean(required=True)


class StompHeaderSchema(GardenBaseSchema):
    key = fields.String(required=True)
    value = fields.String(required=True)


class StompConnectionParamsSchema(GardenBaseSchema):
    ssl = fields.Nested("StompSSLParamsSchema", required=True)
    headers = fields.List(fields.Nested("StompHeaderSchema"), required=False)
    host = fields.String(required=True)
    port = fields.Integer(
        required=True,
        validate=_port_validator,
        error_messages={
            **fields.Field.default_error_messages,
            **{"validator_failed": "Value out of range for ports"},
        },
    )
    send_destination = fields.String(required=False, allow_none=True)
    subscribe_destination = fields.String(required=False, allow_none=True)
    username = fields.String(required=False, allow_none=True)
    password = fields.String(required=False, allow_none=True)


class GardenConnectionsParamsSchema(GardenBaseSchema):
    http = fields.Nested("HttpConnectionParamsSchema", allow_none=True)
    stomp = fields.Nested("StompConnectionParamsSchema", allow_none=True)


class GardenSchema(GardenBaseSchema):
    id = fields.Str(allow_none=True)
    name = fields.Str(allow_none=False)
    status = fields.Str(allow_none=True)
    status_info = fields.Nested(StatusInfoSchema, allow_none=True)
    connection_type = fields.Str(allow_none=False)
    connection_params = fields.Nested(GardenConnectionsParamsSchema, allow_none=True)
    namespaces = fields.List(fields.Str(), allow_none=True)
    systems = fields.Nested(SystemSchema, many=True, allow_none=True)

    @post_load
    def make_object(self, data):
        return BrewtilsGarden(**data)
