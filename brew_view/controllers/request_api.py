import datetime
import logging

from bg_utils.models import Request
from bg_utils.parser import BeerGardenSchemaParser

from brew_view.base_handler import BaseHandler
from brewtils.errors import ModelValidationError
from brewtils.models import Events, Request as BrewtilsRequest


class RequestAPI(BaseHandler):

    parser = BeerGardenSchemaParser()
    logger = logging.getLogger(__name__)

    def get(self, request_id):
        """
        ---
        summary: Retrieve a specific Request
        parameters:
          - name: request_id
            in: path
            required: true
            description: The ID of the Request
            type: string
        responses:
          200:
            description: Request with the given ID
            schema:
              $ref: '#/definitions/Request'
          404:
            $ref: '#/definitions/404Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Requests
        """
        self.logger.debug("Getting Request: %s", request_id)

        req = Request.objects.get(id=str(request_id))
        req.children = Request.objects(parent=req)

        self.write(self.parser.serialize_request(req, to_string=False))

    def _update_completed_request_metrics(self, request):
        # We don't use _measure_latency here because the request times are
        # stored in UTC and we need to make sure we're comparing apples to
        # apples.
        latency = (datetime.datetime.utcnow() - request.updated_at).total_seconds()
        common_labels = {
            'system': request.system,
            'system_version': request.system_version,
            'instance_name': request.instance_name,
        }

        self.completed_request_counter.labels(
            command=request.command,
            status=request.status,
            **common_labels
        ).inc()
        self.plugin_command_latency.labels(
            command=request.command,
            status=request.status,
            **common_labels
        ).observe(latency)

        self.in_progress_request_gauge.labels(**common_labels).dec()
        self.queued_request_gauge.labels(**common_labels).dec()

    def patch(self, request_id):
        """
        ---
        summary: Partially update a Request
        description: |
          The body of the request needs to contain a set of instructions detailing the updates to
          apply. Currently the only operation supported is `replace`, with paths `/status`,
          `/output`, and `/error_class`:
          ```JSON
          {
            "operations": [
              { "operation": "replace", "path": "/status", "value": "" }
            ]
          }
          ```
        parameters:
          - name: request_id
            in: path
            required: true
            description: The ID of the Request
            type: string
          - name: patch
            in: body
            required: true
            description: Instructions for how to update the Request
            schema:
              $ref: '#/definitions/Patch'
        responses:
          200:
            description: Request with the given ID
            schema:
              $ref: '#/definitions/Request'
          400:
            $ref: '#/definitions/400Error'
          404:
            $ref: '#/definitions/404Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Requests
        """
        req = Request.objects.get(id=request_id)
        operations = self.parser.parse_patch(self.request.decoded_body, many=True, from_string=True)

        # We note the status before the operations, because it is possible for the operations to
        # update the status of the request. In that case, because the updates are coming in in a
        # single request it is okay to update the output or error_class. Ideally this would be
        # handled correctly when we better integrate PatchOperations with their models.
        status_before = req.status

        for op in operations:
            if op.operation == 'replace':
                if op.path == '/status':
                    if op.value.upper() in BrewtilsRequest.STATUS_LIST:
                        req.status = op.value.upper()

                        if op.value.upper() == 'IN_PROGRESS':
                            self.request.event.name = Events.REQUEST_STARTED.name
                            self.in_progress_request_gauge.labels(
                                system=req.system,
                                system_version=req.system_version,
                                instance_name=req.instance_name,
                            ).inc()
                        elif op.value.upper() in BrewtilsRequest.COMPLETED_STATUSES:
                            self.request.event.name = Events.REQUEST_COMPLETED.name
                            self._update_completed_request_metrics(req)
                    else:
                        error_msg = "Unsupported status value '%s'" % op.value
                        self.logger.warning(error_msg)
                        raise ModelValidationError(error_msg)
                elif op.path == '/output':
                    if req.output == op.value:
                        continue

                    if status_before in Request.COMPLETED_STATUSES:
                        raise ModelValidationError("Cannot update output for a request "
                                                   "that is already completed")
                    req.output = op.value
                elif op.path == '/error_class':
                    if req.error_class == op.value:
                        continue

                    if status_before in Request.COMPLETED_STATUSES:
                        raise ModelValidationError("Cannot update error_class for a "
                                                   "request that is already completed")
                    req.error_class = op.value
                    self.request.event.error = True
                else:
                    error_msg = "Unsupported path '%s'" % op.path
                    self.logger.warning(error_msg)
                    raise ModelValidationError(error_msg)
            else:
                error_msg = "Unsupported operation '%s'" % op.operation
                self.logger.warning(error_msg)
                raise ModelValidationError(error_msg)

        req.save()

        self.request.event_extras = {'request': req, 'patch': operations}

        self.write(self.parser.serialize_request(req, to_string=False))
