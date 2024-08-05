# -*- coding: utf-8 -*-
from brewtils.errors import ModelValidationError
from brewtils.models import Operation, Permissions, System
from brewtils.schema_parser import SchemaParser
from brewtils.schemas import SystemSchema as BrewtilsSystemSchema

from beer_garden.api.http.handlers import AuthorizationHandler
from beer_garden.metrics import collect_metrics
from beer_garden.api.http.schemas.v1.system import SystemSansQueueSchema


def _remove_queue_info(response: str, many: bool = False) -> str:
    """Strips out the queue_type and queue_info from the Systems response json.

    This exists because the natural path of getting System data is so tightly integrated
    with the brewtils schemas and the back and forth between mongoengine and brewtils
    models that attempting to change the schema used for initial serialization is too
    risky. Instead, this takes the serialized response and just runs it through another
    Schema that strips out the queue info.
    """
    system_data = SystemSansQueueSchema(many=many).loads(response).data
    return SystemSansQueueSchema(many=many).dumps(system_data).data


class SystemAPI(AuthorizationHandler):

    @collect_metrics(transaction_type="API", group="SystemAPI")
    async def get(self, system_id):
        """
        ---
        summary: Retrieve a specific System
        parameters:
          - name: system_id
            in: path
            required: true
            description: The ID of the System
            type: string
          - name: include_commands
            in: query
            required: false
            description: Include the System's commands in the response
            type: boolean
            default: true
        responses:
          200:
            description: System with the given ID
            schema:
              $ref: '#/definitions/System'
          404:
            $ref: '#/definitions/404Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Systems
        """

        system = self.get_or_raise(System, id=system_id)

        # This is only here because of backwards compatibility
        include_commands = (
            self.get_query_argument("include_commands", default="").lower() != "false"
        )

        if not include_commands:
            system.commands = []

        response = SystemSansQueueSchema().dump(system).data

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(response)

    @collect_metrics(transaction_type="API", group="SystemAPI")
    async def delete(self, system_id):
        """
        Will give Bartender a chance to remove instances of this system from the
        registry but will always delete the system regardless of whether the Bartender
        operation succeeds.
        ---
        summary: Delete a specific System
        description: Will remove instances of local plugins from the registry, clear
            and remove message queues, and remove the system from the database.
        parameters:
          - name: system_id
            in: path
            required: true
            description: The ID of the System
            type: string
          - name: force
            in: query
            required: false
            description: Flag indicating whether to force delete
            type: boolean
            default: false
        responses:
          204:
            description: System has been successfully deleted
          404:
            $ref: '#/definitions/404Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Systems
        """
        self.minimum_permission = Permissions.PLUGIN_ADMIN.name
        _ = self.get_or_raise(System, id=system_id)

        await self.process_operation(
            Operation(
                operation_type="SYSTEM_DELETE",
                args=[system_id],
                kwargs={
                    "force": self.get_argument("force", default="").lower() == "true"
                },
            ),
            filter_results=False,
        )

        self.set_status(204)

    @collect_metrics(transaction_type="API", group="SystemAPI")
    async def patch(self, system_id):
        """
        ---
        summary: Partially update a System
        description: |
          The body of the request needs to contain a set of instructions detailing the
          updates to apply.
          Currently supported operations are below:
          ```JSON
          [
            { "operation": "add", "path": "/instance", "value": "" },
            { "operation": "replace", "path": "/commands", "value": "" },
            { "operation": "replace", "path": "/description", "value": "new description"},
            { "operation": "replace", "path": "/display_name", "value": "new display name"},
            { "operation": "replace", "path": "/icon_name", "value": "new icon name"},
            { "operation": "replace", "path": "/groups", "value": ["group"]},
            { "operation": "update", "path": "/metadata", "value": {"foo": "bar"}}
          ]
          ```
          Where `value` is a list of new Commands.
        parameters:
          - name: system_id
            in: path
            required: true
            description: The ID of the System
            type: string
          - name: patch
            in: body
            required: true
            description: Instructions for how to update the System
            schema:
              $ref: '#/definitions/Patch'
        responses:
          200:
            description: System with the given ID
            schema:
              $ref: '#/definitions/System'
          400:
            $ref: '#/definitions/400Error'
          404:
            $ref: '#/definitions/404Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Systems
        """
        self.minimum_permission = Permissions.PLUGIN_ADMIN.name
        _ = self.get_or_raise(System, id=system_id)

        kwargs = {}
        do_reload = False

        response = ""

        for op in SchemaParser.parse_patch(self.request.decoded_body, from_string=True):
            if op.operation == "replace":
                if op.path == "/commands":
                    kwargs["new_commands"] = SchemaParser.parse_command(
                        op.value, many=True
                    )
                elif op.path in [
                    "/description",
                    "/icon_name",
                    "/display_name",
                    "/template",
                    "/groups",
                ]:
                    kwargs[op.path.strip("/")] = op.value
                else:
                    raise ModelValidationError(
                        f"Unsupported path for replace '{op.path}'"
                    )

            elif op.operation == "add":
                if op.path == "/instance":
                    if not kwargs.get("add_instances"):
                        kwargs["add_instances"] = []

                    kwargs["add_instances"].append(
                        SchemaParser.parse_instance(op.value)
                    )
                else:
                    raise ModelValidationError(f"Unsupported path for add '{op.path}'")

            elif op.operation == "update":
                if op.path == "/metadata":
                    kwargs["metadata"] = op.value
                else:
                    raise ModelValidationError(
                        f"Unsupported path for update '{op.path}'"
                    )

            elif op.operation == "reload":
                do_reload = True

            else:
                raise ModelValidationError(f"Unsupported operation '{op.operation}'")

        if kwargs:
            response = _remove_queue_info(
                await self.process_operation(
                    Operation(
                        operation_type="SYSTEM_UPDATE", args=[system_id], kwargs=kwargs
                    )
                )
            )

        if do_reload:
            await self.process_operation(
                Operation(operation_type="SYSTEM_RELOAD", args=[system_id])
            )

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(response)


class SystemListAPI(AuthorizationHandler):
    REQUEST_FIELDS = set(BrewtilsSystemSchema.get_attribute_names())

    @collect_metrics(transaction_type="API", group="SystemListAPI")
    async def get(self):
        """
        ---
        summary: Retrieve all Systems
        description: |
          This endpoint allows for querying Systems.

          There are several parameters that control which fields are returned
          and what information is available. Things to be aware of:

          * The `include_commands` parameter is __deprecated__. Don't use it.
            Use `exclude_fields=commands` instead.

          * It's possible to specify `include_fields` _and_ `exclude_fields`.
            This doesn't make a lot of sense, but you can do it. If the same
            field is in both `exclude_fields` takes priority (the field will
            NOT be included in the response).

          Systems matching specific criteria can be filtered using additional
          query parameters. This is a very basic capability:

          * ?name=foo&version=1.0.0
            This will return the system named 'foo' with version '1.0.0'
          * ?name=foo&name=bar
            This will not do what you expect: only return the system named
            'bar' will be returned.
        parameters:
          - name: include_fields
            in: query
            required: false
            description: Specify fields to include in the response. All other
              fields will be excluded.
            type: array
            collectionFormat: csv
            items:
              type: string
          - name: exclude_fields
            in: query
            required: false
            description: Specify fields to exclude from the response
            type: array
            collectionFormat: csv
            items:
              type: string
          - name: dereference_nested
            in: query
            required: false
            description: Commands and instances will be an object id
            type: boolean
            default: true
          - name: filter_latest
            in: query
            required: false
            description: Filter latest system versions
            type: boolean
            default: false
        responses:
          200:
            description: All Systems
            schema:
              type: array
              items:
                $ref: '#/definitions/System'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Systems
        """

        permitted_objects_filter = self.permitted_objects_filter(System)

        order_by = self.get_query_argument("order_by", None)

        dereference_nested = self.get_query_argument("dereference_nested", None)
        if dereference_nested is None:
            dereference_nested = True
        else:
            dereference_nested = bool(dereference_nested.lower() == "true")

        filter_latest = self.get_query_argument("filter_latest", None)
        if filter_latest is None:
            filter_latest = False
        else:
            filter_latest = bool(filter_latest.lower() == "true")

        include_fields = self.get_query_argument("include_fields", None)
        if include_fields:
            include_fields = set(include_fields.split(",")) & self.REQUEST_FIELDS

        exclude_fields = self.get_query_argument("exclude_fields", None)
        if exclude_fields:
            exclude_fields = set(exclude_fields.split(",")) & self.REQUEST_FIELDS

        # TODO - Handle multiple query arguments with the same key
        # for example: (?name=foo&name=bar) ... what should that mean?
        # Need to use self.request.query_arguments to get all the query args
        filter_params = {}
        for key in self.request.query_arguments:
            if key in self.REQUEST_FIELDS:
                filter_params[key] = self.get_query_argument(key)

        serialize_kwargs = {"to_string": True, "many": True}
        if include_fields:
            serialize_kwargs["only"] = include_fields
        if exclude_fields:
            serialize_kwargs["exclude"] = exclude_fields

        response = await self.process_operation(
            Operation(
                operation_type="SYSTEM_READ_ALL",
                kwargs={
                    "serialize_kwargs": serialize_kwargs,
                    "q_filter": permitted_objects_filter,
                    "filter_params": filter_params,
                    "order_by": order_by,
                    "include_fields": include_fields,
                    "exclude_fields": exclude_fields,
                    "dereference_nested": dereference_nested,
                    "filter_latest": filter_latest,
                },
            )
        )

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(_remove_queue_info(response, many=True))

    @collect_metrics(transaction_type="API", group="SystemListAPI")
    async def post(self):
        """
        ---
        summary: Create a new System or update an existing System
        description: |
            If the System does not exist it will be created. If the System
            already exists it will be updated (assuming it passes validation).
        parameters:
          - name: system
            in: body
            description: The System definition to create / update
            schema:
              $ref: '#/definitions/System'
        responses:
          200:
            description: An existing System has been updated
            schema:
              $ref: '#/definitions/System'
          201:
            description: A new System has been created
            schema:
              $ref: '#/definitions/System'
          400:
            $ref: '#/definitions/400Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Systems
        """
        self.minimum_permission = Permissions.PLUGIN_ADMIN.name
        system = SchemaParser.parse_system(self.request.decoded_body, from_string=True)

        self.verify_user_permission_for_object(system)

        response = await self.process_operation(
            Operation(
                operation_type="SYSTEM_CREATE",
                args=[system],
            )
        )
        self.set_status(201)
        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(_remove_queue_info(response))
