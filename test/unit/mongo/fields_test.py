from bg_utils.mongo.fields import DummyField


class TestDummyField(object):
    def test_to_python(self):
        field = DummyField()
        assert field.to_python("value") == "value"

    def test_to_mongo(self):
        field = DummyField()
        assert field.to_mongo("value") is None
