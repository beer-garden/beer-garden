import json

from brewtils.models import Operation, Permissions

from beer_garden.api.http.handlers import AuthorizationHandler
from beer_garden.garden import local_garden


class DBCleanupMemoryAPI(AuthorizationHandler):
    # Cleanup memory usage i.e. compact
    async def post(self):
        """
        ---
        summary: Cleanup DB Memory Usage
        description: |
          The body of the request needs to contain a set of instructions with one or
          more collections (optional) and whether to execute db operation.
          Execute maps to inverse of dryRun in Mongo8 and newer. Older
          versions return statistics about a collection.

          ```Examples
          {} - Get memory usage stats for all collections
          { "collections": ["user"]} - Get memory usage for collection user
          { "collections": ["user"], "execute": "true" } - Run operation on user collection
          { "collections": [], "execute": "true" } - Run operation on all collections
          { "execute": "true" } - Run operation on all collections
          ```
        parameters:
          - name: body
            in: body
            required: false
            description: Body with params
            type: object
        responses:
          200:
            description: Operation completed successfully
          400:
            $ref: '#/definitions/400Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Cleanup
        """
        self.minimum_permission = Permissions.GARDEN_ADMIN.name
        self.verify_user_permission_for_object(local_garden())

        body = json.loads(self.request.body.decode("utf-8"))
        collections = body.get("collections", [])
        execute = body.get("execute", "").lower() == "true"

        # Mongodb compact operation is blocking
        response = await self.process_operation(
            Operation(
                operation_type="CLEANUP_DB_COMPACT",
                kwargs={"collection_names": collections, "execute": execute},
            )
        )

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(response)


class DBCleanupIndexesAPI(AuthorizationHandler):
    # Rebuild indexes
    # POST and tell it what to do
    async def post(self):
        """
        ---
        summary: Rebuild Indexes
        description: |
          The body of the request needs to contain a set of instructions with one or
          more collections (optional) and whether to execute db operation

          ```Examples
          {} - Get memory usage stats for all collections
          { "collections": ["user"]} - Get memory usage for collection user
          { "collections": ["user"], "execute": "true" } - Run  operation on user collection
          { "collections": [], "execute": "true" } - Run operation on all collections
          { "execute": "true" } - Run operation on all collections
          ```
        parameters:
          - name: body
            in: body
            required: false
            description: Body with params
            type: object
        responses:
          200:
            description: Operation completed successfully
          400:
            $ref: '#/definitions/400Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Cleanup
        """
        self.minimum_permission = Permissions.GARDEN_ADMIN.name
        self.verify_user_permission_for_object(local_garden())

        body = json.loads(self.request.body.decode("utf-8"))
        collections = body.get("collections", [])
        execute = body.get("execute", "").lower() == "true"

        # Mongodb reIndex operation is blocking
        response = await self.process_operation(
            Operation(
                operation_type="CLEANUP_DB_REINDEX",
                kwargs={"collection_names": collections, "execute": execute},
            )
        )

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(response)
