import pytest

try:
    from helper import RequestGenerator, setup_easy_client
except ImportError:
    from ..helper import RequestGenerator, setup_easy_client


@pytest.fixture(scope="class")
def request_generator(request, system_spec):
    request.cls.request_generator = RequestGenerator(**system_spec)


@pytest.fixture(scope="class")
def easy_client(request):
    request.cls.easy_client = setup_easy_client()
    return request.cls.easy_client
