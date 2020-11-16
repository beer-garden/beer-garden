# -*- coding: utf-8 -*-
import asyncio
import datetime
import re
import socket

from brewtils.errors import (
    AuthorizationRequired,
    ConflictError,
    ModelError,
    ModelValidationError,
    RequestForbidden,
    RequestPublishException,
    WaitExceededError,
)
from jwt.exceptions import ExpiredSignatureError, InvalidSignatureError
from mongoengine.errors import (
    DoesNotExist,
    NotUniqueError,
    ValidationError as MongoValidationError,
)
from pymongo.errors import DocumentTooLarge
from tornado.web import HTTPError, RequestHandler

import beer_garden.api.http
import beer_garden.config as config
import beer_garden.db.mongo.models
from beer_garden.api.http.authorization import (
    AuthMixin,
    basic_auth,
    bearer_auth,
    coalesce_permissions,
)
from beer_garden.api.http.metrics import http_api_latency_total
from beer_garden.errors import (
    EndpointRemovedException,
    NotFoundException,
    RoutingRequestException,
)


async def event_wait(evt, timeout):
    """Helper method to add a timeout to an asyncio wait"""
    try:
        await asyncio.wait_for(evt.wait(), timeout)
    except asyncio.TimeoutError:
        pass
    return evt.is_set()


class BaseHandler(AuthMixin, RequestHandler):
    """Base handler from which all handlers inherit"""

    auth_providers = frozenset([bearer_auth, basic_auth])

    MONGO_ID_PATTERN = r".*/([0-9a-f]{24}).*"
    REFRESH_COOKIE_NAME = "refresh_id"
    REFRESH_COOKIE_EXP = 14

    charset_re = re.compile(r"charset=(.*)$")

    error_map = {
        MongoValidationError: {"status_code": 400},
        ModelError: {"status_code": 400},
        RoutingRequestException: {"status_code": 400},
        ExpiredSignatureError: {"status_code": 401},
        AuthorizationRequired: {"status_code": 401},
        RequestForbidden: {"status_code": 403},
        InvalidSignatureError: {"status_code": 403},
        DoesNotExist: {"status_code": 404, "message": "Resource does not exist"},
        NotFoundException: {"status_code": 404},
        WaitExceededError: {"status_code": 408, "message": "Max wait time exceeded"},
        ConflictError: {"status_code": 409},
        NotUniqueError: {"status_code": 409, "message": "Resource already exists"},
        EndpointRemovedException: {"status_code": 410, "message": "Endpoint removed"},
        DocumentTooLarge: {"status_code": 413, "message": "Resource too large"},
        RequestPublishException: {"status_code": 502},
        socket.timeout: {"status_code": 504, "message": "Backend request timed out"},
    }

    def get_refresh_id_from_cookie(self):
        token_id = self.get_secure_cookie(self.REFRESH_COOKIE_NAME)
        if token_id:
            return token_id.decode()
        return None

    def _get_user_from_cookie(self):
        refresh_id = self.get_refresh_id_from_cookie()
        if not refresh_id:
            return None

        token = beer_garden.db.mongo.models.RefreshToken.objects.get(id=refresh_id)
        now = datetime.datetime.utcnow()
        if not token or token.expires < now:
            return None

        principal = token.get_principal()
        if not principal:
            return None

        _, principal.permissions = coalesce_permissions(principal.roles)
        token.expires = now + datetime.timedelta(days=self.REFRESH_COOKIE_EXP)
        token.save()
        return principal

    def get_current_user(self):
        user = AuthMixin.get_current_user(self)
        if not user or user == beer_garden.api.http.anonymous_principal:
            cookie_user = self._get_user_from_cookie()
            if cookie_user:
                user = cookie_user
        return user

    def set_default_headers(self):
        """Headers set here will be applied to all responses"""
        self.set_header("BG-Version", beer_garden.__version__)

        if config.get("ui.cors_enabled"):
            self.set_header("Access-Control-Allow-Origin", "*")
            self.set_header("Access-Control-Allow-Headers", "Content-Type")
            self.set_header(
                "Access-Control-Allow-Methods", "GET, POST, PATCH, DELETE, OPTIONS"
            )

    @property
    def prometheus_endpoint(self):
        """Removes Mongo ID from endpoint."""
        to_return = self.request.path.rstrip("/")
        for mongo_id in re.findall(self.MONGO_ID_PATTERN, self.request.path):
            to_return = to_return.replace(mongo_id, "<ID>")
        return to_return

    @property
    def client(self):
        return self.settings["client"]

    def prepare(self):
        """Called before each verb handler"""

        # Used for calculating request handling duration
        self.request.created_time = datetime.datetime.utcnow()

        content_type = self.request.headers.get("content-type", "")
        if self.request.method.upper() in ["POST", "PATCH"] and content_type:
            content_type = content_type.split(";")

            self.request.mime_type = content_type[0]
            if self.request.mime_type not in [
                "application/json",
                "application/x-www-form-urlencoded",
            ]:
                raise ModelValidationError("Unsupported or missing content-type header")

            # Attempt to parse out the charset and decode the body, default to utf-8
            charset = "utf-8"
            if len(content_type) > 1:
                search_result = self.charset_re.search(content_type[1])
                if search_result:
                    charset = search_result.group(1)
            self.request.charset = charset
            self.request.decoded_body = self.request.body.decode(charset)

    def on_finish(self):
        """Called after a handler completes processing"""
        # Latency measurement for blocking request creation just muddies the waters
        if not getattr(self.request, "ignore_latency", False):
            timedelta = datetime.datetime.utcnow() - self.request.created_time

            http_api_latency_total.labels(
                method=self.request.method.upper(),
                route=self.prometheus_endpoint,
                status=self.get_status(),
            ).observe(timedelta.total_seconds())

    def options(self, *args, **kwargs):

        if config.get("ui.cors_enabled"):
            self.set_status(204)
        else:
            raise HTTPError(403, reason="CORS is disabled")

    def write_error(self, status_code, **kwargs):
        """Transform an exception into a response.

        This protects controllers from having to write a lot of the same code over and
        over and over. Controllers can, of course, overwrite error handlers and return
        their own responses if necessary, but generally, this is where error handling
        should occur.

        When an exception is handled this function makes two passes through error_map.
        The first pass is to see if the exception type can be matched exactly. If there
        is no exact type match the second pass will attempt to match using isinstance.
        If a message is provided in the error_map it takes precedence over the
        exception message.

        ***NOTE*** Nontrivial inheritance trees will almost definitely break. This is a
        BEST EFFORT using a simple isinstance check on an unordered data structure. So
        if an exception class has both a parent and a grandparent in the error_map
        there is no guarantee about which message / status code will be chosen. The
        same applies to exceptions that use multiple inheritance.

        ***LOGGING***
        An exception raised in a controller method will generate logging to the
        tornado.application logger that includes a stacktrace. That logging occurs
        before this method is invoked. The result of this method will generate logging
        to the tornado.access logger as usual. So there is no need to do additional
        logging here as the 'real' exception will already have been logged.

        :param status_code: a status_code that will be used if no match is found in the
        error map
        :return: None
        """
        code = 0
        message = ""

        if "exc_info" in kwargs:
            typ3 = kwargs["exc_info"][0]
            e = kwargs["exc_info"][1]

            error_dict = None
            if typ3 in self.error_map.keys():
                error_dict = self.error_map[typ3]
            else:
                for error_type in self.error_map.keys():
                    if isinstance(e, error_type):
                        error_dict = self.error_map[error_type]
                        break

            if error_dict:
                # Thrift exceptions should have a message attribute
                message = error_dict.get("message", getattr(e, "message", str(e)))
                code = error_dict.get("status_code", 500)

            elif config.get("ui.debug_mode"):
                message = str(e)

        code = code or status_code or 500
        message = message or (
            "Encountered unknown exception. Please check "
            "with your System Administrator."
        )

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.set_status(code)
        self.finish({"message": message})
