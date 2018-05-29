import base64
import re
import socket

from mongoengine.errors import DoesNotExist, NotUniqueError, ValidationError as MongoValidationError
from passlib.apps import custom_app_context
from thriftpy.thrift import TException
from tornado.web import HTTPError, RequestHandler

import bg_utils
import brew_view
from bg_utils.models import Principal
from brewtils.errors import ModelError, ModelValidationError, RequestPublishException
from brewtils.models import Event


class BaseHandler(RequestHandler):
    """Base handler from which all handlers inherit. Enables CORS and error handling."""

    def __init__(self, *args, **kwargs):
        super(BaseHandler, self).__init__(*args, **kwargs)

        self.charset_re = re.compile(r'charset=(.*)$')

        self.error_map = {
            MongoValidationError: {'status_code': 400},
            ModelError: {'status_code': 400},
            bg_utils.bg_thrift.InvalidSystem: {'status_code': 400},
            DoesNotExist: {'status_code': 404, 'message': 'Resource does not exist'},
            NotUniqueError: {'status_code': 409, 'message': 'Resource already exists'},

            RequestPublishException: {'status_code': 502},
            bg_utils.bg_thrift.BaseException: {'status_code': 502, 'message': 'An error occurred '
                                                                              'on the backend'},
            TException: {'status_code': 503, 'message': 'Could not connect to Bartender'},
            socket.timeout: {'status_code': 504, 'message': 'Backend request timed out'},
        }

    def set_default_headers(self):
        """Enable CORS by setting the access control header"""

        if brew_view.config.cors_enabled:
            self.set_header("Access-Control-Allow-Origin", "*")
            self.set_header("Access-Control-Allow-Headers", "Content-Type")
            self.set_header("Access-Control-Allow-Methods", "GET, POST, PATCH, DELETE, OPTIONS")

    def get_current_user(self):
        session_cookie = self.get_secure_cookie('session')
        if session_cookie:
            return Principal.objects.get(id=session_cookie.decode('utf-8'))
        else:
            return self.parse_basic_auth()

    def parse_basic_auth(self):
        auth_header = self.request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Basic '):
            auth_decoded = base64.b64decode(auth_header[6:]).decode()
            username, password = auth_decoded.split(':')

            # In this case return 403 to prevent an attacker from being able to
            # enumerate a list of usernames
            try:
                principal = Principal.objects.get(username=username)
            except DoesNotExist:
                raise HTTPError(403, reason='Nah son')

            if custom_app_context.verify(password, principal.hash):
                return principal
            else:
                raise HTTPError(403, reason='Nah son')
        else:
            return None

    def prepare(self):
        """Called before each verb handler"""
        # This is used for sending event notifications
        self.request.event = Event()
        self.request.event_extras = {}

        content_type = self.request.headers.get('content-type', '')
        if self.request.method.upper() in ['POST', 'PATCH'] and content_type:
            content_type = content_type.split(';')

            self.request.mime_type = content_type[0]
            if self.request.mime_type not in ['application/json',
                                              'application/x-www-form-urlencoded']:
                raise ModelValidationError('Unsupported or missing content-type header')

            # Attempt to parse out the charset and decode the body, default to utf-8
            charset = 'utf-8'
            if len(content_type) > 1:
                search_result = self.charset_re.search(content_type[1])
                if search_result:
                    charset = search_result.group(1)
            self.request.charset = charset
            self.request.decoded_body = self.request.body.decode(charset)

    def on_finish(self):
        """Called after a handler completes processing"""
        if self.request.event.name:
            brew_view.event_publishers.publish_event(self.request.event,
                                                     **self.request.event_extras)

    def options(self, *args, **kwargs):

        if brew_view.config.cors_enabled:
            self.set_status(204)
        else:
            raise HTTPError(403, reason='CORS is disabled')

    def write_error(self, status_code, **kwargs):
        """Transform an exception into a response.

        This protects controllers from having to write a lot of the same code over and over and
        over. Controllers can, of course, overwrite error handlers and return their own responses
        if necessary, but generally, this is where error handling should occur.

        When an exception is handled this function makes two passes through error_map. The first
        pass is to see if the exception type can be matched exactly. If there is no exact type
        match the second pass will attempt to match using isinstance. If a message is provided in
        the error_map it takes precedence over the exception message.

        ***NOTE*** Nontrivial inheritance trees will almost definitely break. This is a BEST EFFORT
        using a simple isinstance check on an unordered data structure. So if an exception class
        has both a parent and a grandparent in the error_map there is no guarantee about which
        message / status code will be chosen. The same applies to exceptions that use multiple
        inheritance.

        ***LOGGING***
        An exception raised in a controller method will generate logging to the tornado.application
        logger that includes a stacktrace. That logging occurs before this method is invoked.
        The result of this method will generate logging to the tornado.access logger as usual.
        So there is no need to do additional logging here as the 'real' exception will already have
        been logged.

        :param status_code: a status_code that will be used if no match is found in the error map
        :return: None
        """
        code = 0
        message = ''

        if 'exc_info' in kwargs:
            typ3 = kwargs['exc_info'][0]
            e = kwargs['exc_info'][1]

            error_dict = None
            if typ3 in self.error_map.keys():
                error_dict = self.error_map[typ3]
            else:
                for error_type in self.error_map.keys():
                    if isinstance(e, error_type):
                        error_dict = self.error_map[error_type]
                        break

            if error_dict:
                code = error_dict.get('status_code', 500)
                message = error_dict.get('message', str(e))

            elif brew_view.config.debug_mode:
                message = str(e)

        code = code or status_code or 500
        message = message or ('Encountered unknown exception. Please check '
                              'with your System Administrator.')

        self.request.event.error = True
        self.request.event.payload = {'message': message}

        self.set_header('Content-Type', 'application/json; charset=UTF-8')
        self.set_status(code)
        self.finish({'message': message})
