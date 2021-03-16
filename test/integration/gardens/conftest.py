import pytest
from brewtils.schema_parser import SchemaParser

from helper import setup_easy_client, RequestGenerator


@pytest.fixture(scope="class")
def request_generator(request, system_spec):
    request.cls.request_generator = RequestGenerator(**system_spec)


@pytest.fixture(scope="class")
def easy_client(request):
    request.cls.easy_client = setup_easy_client()
    return request.cls.easy_client

@pytest.fixture(scope="class")
def parser():
    return SchemaParser()