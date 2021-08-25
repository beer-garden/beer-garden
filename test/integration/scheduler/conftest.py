import pytest

try:
    from helper import RequestGenerator, setup_easy_client
except (ImportError, ValueError):
    from ..helper import RequestGenerator, setup_easy_client  # noqa


@pytest.fixture(scope="class")
def easy_client(request):
    request.cls.easy_client = setup_easy_client()
    return request.cls.easy_client
