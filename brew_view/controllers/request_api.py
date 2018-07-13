import datetime
import logging

import brew_view
from bg_utils.models import Request, Job
from bg_utils.parser import BeerGardenSchemaParser
from brew_view.authorization import authenticated, Permissions
from brew_view.base_handler import BaseHandler
from brewtils.errors import ModelValidationError
from brewtils.models import Events, Request as BrewtilsRequest


class RequestAPI(BaseHandler):

    parser = BeerGardenSchemaParser()
    logger = logging.getLogger(__name__)

    @authenticated(permissions=[Permissions.REQUEST_READ])
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

    @authenticated(permissions=[Permissions.REQUEST_UPDATE])
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
        wait_condition = None

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

                        elif op.value.upper() in BrewtilsRequest.COMPLETED_STATUSES:
                            self.request.event.name = Events.REQUEST_COMPLETED.name

                            if request_id in brew_view.request_map:
                                wait_condition = brew_view.request_map[request_id]
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
        self._update_metrics(req, status_before)
        self._update_job_numbers(req, status_before)

        if wait_condition:
            wait_condition.notify()

        self.request.event_extras = {'request': req, 'patch': operations}

        self.write(self.parser.serialize_request(req, to_string=False))

    def _update_job_numbers(self, request, status_before):
        if (
            not request.metadata.get('_bg_job_id') or
            status_before == request.status or
            request.status not in Request.COMPLETED_STATUSES
        ):
            return

        try:
            job_id = request.metadata.get('_bg_job_id')
            document = Job.objects.get(id=job_id)
            if request.status == 'ERROR':
                document.error_count += 1
            elif request.status == 'SUCCESS':
                document.success_count += 1
            document.save()
        except Exception as exc:
            self.logger.warning('Could not update job counts.')
            self.logger.exception(exc)

    def _update_metrics(self, request, status_before):
        """Update metrics associated with this new request.

        We have already confirmed that this request has had a valid state
        transition because updating the status verifies that the updates are
        correct.

        In addition, this call is happening after the save to the
        database. Now we just need to update the metrics.
        """
        if (
            status_before == request.status or
            status_before in BrewtilsRequest.COMPLETED_STATUSES
        ):
            return

        labels = {
            'system': request.system,
            'system_version': request.system_version,
            'instance_name': request.instance_name,
        }

        if status_before == 'CREATED':
            self.queued_request_gauge.labels(**labels).dec()
        elif status_before == 'IN_PROGRESS':
            self.in_progress_request_gauge.labels(**labels).dec()

        if request.status == 'IN_PROGRESS':
            self.in_progress_request_gauge.labels(**labels).inc()

        elif request.status in BrewtilsRequest.COMPLETED_STATUSES:
            # We don't use _measure_latency here because the request times are
            # stored in UTC and we need to make sure we're comparing apples to
            # apples.
            latency = (datetime.datetime.utcnow() - request.created_at).total_seconds()
            labels['command'] = request.command
            labels['status'] = request.status

            self.completed_request_counter.labels(**labels).inc()
            self.plugin_command_latency.labels(**labels).observe(latency)
