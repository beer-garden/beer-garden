import pytest

try:
    from helper import setup_easy_client, RequestGenerator
except:
    from ..helper import setup_easy_client, RequestGenerator


@pytest.fixture(scope="class")
def easy_client(request):
    request.cls.easy_client = setup_easy_client()
    return request.cls.easy_client
