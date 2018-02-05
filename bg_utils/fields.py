from mongoengine.base import BaseField
from mongoengine import EmbeddedDocument, DateTimeField


class DummyField(BaseField):
    """Field that is used for objects that don't get written to the Mongo database"""

    def to_python(self, value):
        return value

    def to_mongo(self, value):
        return None


class StatusInfo(EmbeddedDocument):
    heartbeat = DateTimeField()
