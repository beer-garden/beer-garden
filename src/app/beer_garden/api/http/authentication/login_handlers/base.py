from abc import ABC, abstractmethod
from typing import Optional

from tornado.httputil import HTTPServerRequest

from beer_garden.db.mongo.models import User


class BaseLoginHandler(ABC):
    """Base class for implementing a login handler for initial authentication"""

    @abstractmethod
    def get_user(self, request: HTTPServerRequest) -> Optional[User]:
        """Implementations of this method are expected to authenticate a user based
        on the supplied requests data and then return the corresponding User object
        """
        pass
