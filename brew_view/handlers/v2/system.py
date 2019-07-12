import bg_utils
from brew_view.authorization import authenticated, Permissions
from brew_view.base_handler import BaseHandler
from brew_view.thrift import ThriftClient
from brewtils.errors import ConflictError
from brewtils.schemas import SystemSchema


class SystemAPI(BaseHandler):
    @authenticated(permissions=[Permissions.SYSTEM_READ])
    async def get(self, namespace, system_id):
        """
        ---
        summary: Retrieve a specific System
        parameters:
          - name: namespace
            in: path
            required: true
            description: The namespace
            type: string
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
        include_commands = (
            self.get_query_argument("include_commands", default="").lower() != "false"
        )

        async with ThriftClient() as client:
            thrift_response = await client.getSystem(
                namespace, system_id, include_commands
            )

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(thrift_response)

    @authenticated(permissions=[Permissions.SYSTEM_DELETE])
    async def delete(self, namespace, system_id):
        """
        Will give Bartender a chance to remove instances of this system from the
        registry but will always delete the system regardless of whether the Bartender
        operation succeeds.
        ---
        summary: Delete a specific System
        description: Will remove instances of local plugins from the registry, clear
            and remove message queues, and remove the system from the database.
        parameters:
          - name: namespace
            in: path
            required: true
            description: The namespace
            type: string
          - name: system_id
            in: path
            required: true
            description: The ID of the System
            type: string
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
        async with ThriftClient() as client:
            await client.removeSystem(namespace, system_id)

        self.set_status(204)

    @authenticated(permissions=[Permissions.SYSTEM_UPDATE])
    async def patch(self, namespace, system_id):
        """
        ---
        summary: Partially update a System
        description: |
          The body of the request needs to contain a set of instructions detailing the
          updates to apply.
          Currently supported operations are below:
          ```JSON
          {
            "operations": [
              { "operation": "replace", "path": "/commands", "value": "" },
              { "operation": "replace", "path": "/description", "value": "new description"},
              { "operation": "replace", "path": "/display_name", "value": "new display name"},
              { "operation": "replace", "path": "/icon_name", "value": "new icon name"},
              { "operation": "update", "path": "/metadata", "value": {"foo": "bar"}}
            ]
          }
          ```
          Where `value` is a list of new Commands.
        parameters:
          - name: namespace
            in: path
            required: true
            description: The namespace
            type: string
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
        async with ThriftClient() as client:
            thrift_response = await client.updateSystem(
                namespace, system_id, self.request.decoded_body
            )

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(thrift_response)


class SystemListAPI(BaseHandler):

    REQUEST_FIELDS = set(SystemSchema.get_attribute_names())

    @authenticated(permissions=[Permissions.SYSTEM_READ])
    async def get(self, namespace):
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
          - name: namespace
            in: path
            required: true
            description: The namespace
            type: string
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
        order_by = self.get_query_argument("order_by", None)

        dereference_nested = self.get_query_argument("dereference_nested", None)
        if dereference_nested is None:
            dereference_nested = True
        else:
            dereference_nested = bool(dereference_nested.lower() == "true")

        include_fields = self.get_query_argument("include_fields", None)
        if include_fields:
            include_fields = set(include_fields.split(",")) & self.REQUEST_FIELDS

        exclude_fields = self.get_query_argument("exclude_fields", None)
        if exclude_fields:
            exclude_fields = set(exclude_fields.split(",")) & self.REQUEST_FIELDS

        # TODO - Handle multiple query arguments with the same key
        # for example: (?name=foo&name=bar) ... what should that mean?
        filter_params = {}

        # Need to use self.request.query_arguments to get all the query args
        for key in self.request.query_arguments:
            if key in self.REQUEST_FIELDS:
                filter_params[key] = self.get_query_argument(key)

        async with ThriftClient() as client:
            thrift_response = await client.querySystems(
                namespace,
                filter_params,
                order_by,
                include_fields,
                exclude_fields,
                dereference_nested,
            )

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(thrift_response)

    @authenticated(permissions=[Permissions.SYSTEM_CREATE])
    async def post(self, namespace):
        """
        ---
        summary: Create a new System or update an existing System
        description: |
            If the System does not exist it will be created. If the System
            already exists it will be updated (assuming it passes validation).
        parameters:
          - name: namespace
            in: path
            required: true
            description: The namespace
            type: string
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
        async with ThriftClient() as client:
            try:
                thrift_response = await client.createSystem(
                    namespace, self.request.decoded_body
                )
            except bg_utils.bg_thrift.ConflictException:
                raise ConflictError() from None

        self.set_status(201)
        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(thrift_response)
