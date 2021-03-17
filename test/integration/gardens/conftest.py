import pytest
from brewtils import get_easy_client
from brewtils.schema_parser import SchemaParser

from ..helper import setup_easy_client, RequestGenerator


@pytest.fixture(scope="class")
def request_generator(request, system_spec):
    request.cls.request_generator = RequestGenerator(**system_spec)


@pytest.fixture(scope="class")
def easy_client(request):
    request.cls.easy_client = setup_easy_client()
    return request.cls.easy_client


@pytest.fixture(scope="class")
def child_easy_client(request):
    request.cls.child_easy_client = get_easy_client(bg_host="localhost",
                                                    bg_port=2347,
                                                    ssl_enabled=False)
    return request.cls.child_easy_client


@pytest.fixture(scope="class")
def parser(request):
    request.cls.parser = SchemaParser()
    return request.cls.parser
