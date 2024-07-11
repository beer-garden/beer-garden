# -*- coding: utf-8 -*-
from mongoengine.base import BaseField


class DummyField(BaseField):
    """Field that is used for objects that don't get written to the Mongo database"""

    def to_python(self, value):
        return value

    def to_mongo(self, value):
        return None
