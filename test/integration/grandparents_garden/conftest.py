import pytest
from brewtils import get_easy_client
from brewtils.schema_parser import SchemaParser
import json
import time

try:
    from ..helper import RequestGenerator, setup_easy_client
except (ImportError, ValueError):
    from helper import RequestGenerator, setup_easy_client


@pytest.fixture(scope="class")
def request_generator(request, system_spec):
    request.cls.request_generator = RequestGenerator(**system_spec)

@pytest.fixture(scope="class")
def child_easy_client(request):
    request.cls.child_easy_client = get_easy_client(
        bg_host="localhost", bg_port=2357, ssl_enabled=False
    )
    return request.cls.child_easy_client

@pytest.fixture(scope="class")
def parent_easy_client(request):
    request.cls.parent_easy_client = get_easy_client(
        bg_host="localhost", bg_port=2347, ssl_enabled=False
    )
    return request.cls.child_easy_client

@pytest.fixture(scope="class")
def grand_parent_easy_client(request):
    request.cls.grand_parent_easy_client = get_easy_client(
        bg_host="localhost", bg_port=2337, ssl_enabled=False
    )
    return request.cls.grand_parent_easy_client

def pytest_sessionstart(session):
    client = EasyClient(
        bg_host="localhost", bg_port=2337, ssl_enabled=False
    ).client

    patches = json.dumps(
            [
                {
                    "operation": "sync",
                    "path": "",
                    "value": "",
                }
            ]
        )

    client.patch_garden("", patches)

    time.sleep(20)


@pytest.fixture(scope="class")
def parser(request):
    request.cls.parser = SchemaParser()
    return request.cls.parser
