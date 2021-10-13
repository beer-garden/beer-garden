from typing import Optional

from tornado.web import HTTPError


class BaseHTTPError(HTTPError):
    """This exception class should be used as the base for all exceptions that will
    be raised in the context of the web app / http api. Raising exceptions based on
    BaseHTTPError ensures that both the correct response is returned to the user
    and that errors are properly logged rather than being output as uncaught exceptions.
    """

    status_code: int = 500
    log_message: Optional[str] = None
    reason: Optional[str] = None

    def __init__(
        self,
        status_code: Optional[int] = None,
        log_message: Optional[str] = None,
        reason: Optional[str] = None,
    ):
        self.status_code = status_code if status_code else self.status_code
        self.log_message = log_message if log_message else self.log_message
        self.reason = reason if reason else self.reason

        super().__init__(
            status_code=self.status_code,
            log_message=self.log_message,
            reason=self.reason,
        )


class BadRequest(BaseHTTPError):
    status_code: int = 400
    reason: str = "Bad request"


class AuthorizationRequired(BaseHTTPError):
    status_code: int = 401
    reason: str = "Authorization required"


class InvalidToken(BaseHTTPError):
    status_code: int = 401
    reason: str = "Authorization token invalid"


class ExpiredToken(BaseHTTPError):
    status_code: int = 401
    reason: str = "Authorization token expired"


class RequestForbidden(BaseHTTPError):
    status_code: int = 403
    reason: str = "Access denied"
