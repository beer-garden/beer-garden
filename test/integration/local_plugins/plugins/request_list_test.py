from concurrent.futures import TimeoutError

import pytest
from brewtils.errors import TimeoutExceededError

from ...helper import setup_system_client, wait_for_response, RequestGenerator


@pytest.mark.usefixtures('easy_client')
class TestRequestListApi(object):

    @staticmethod
    @pytest.fixture
    def echo_generator():
        return RequestGenerator(
            system='echo',
            system_version='3.0.0.dev0',
            instance_name='default',
            command='say',
        )

    def test_get_requests(self, echo_generator):
        # Make a couple of requests just to ensure there are some
        request_1 = echo_generator.generate_request(
            parameters={"message": "test_string", "loud": True})
        request_2 = echo_generator.generate_request(
            parameters={"message": "test_string", "loud": False})
        wait_for_response(self.easy_client, request_1)
        wait_for_response(self.easy_client, request_2)

        response = self.easy_client.find_requests(length=2)
        assert len(response) == 2

        # Make sure we don't get an empty object (Brew-view 2.3.8)
        assert response[0].command is not None


@pytest.mark.usefixtures('easy_client')
class TestEasyClient(object):

    @staticmethod
    @pytest.fixture
    def sleeper_generator():
        return RequestGenerator(
            system='sleeper',
            system_version='3.0.0.dev0',
            instance_name='default',
            command='sleep',
        )

    def test_no_wait(self, sleeper_generator):
        req = sleeper_generator.generate_request(parameters={"amount": 1})
        response = self.easy_client.create_request(req)
        assert response.status in ["CREATED", "IN_PROGRESS"]

    def test_wait_success(self, sleeper_generator):
        req = sleeper_generator.generate_request(parameters={"amount": 1})
        response = self.easy_client.create_request(req, blocking=True)
        assert response.status == "SUCCESS"

    def test_wait_timeout(self, sleeper_generator):
        req = sleeper_generator.generate_request(parameters={"amount": 2})

        with pytest.raises(TimeoutExceededError):
            self.easy_client.create_request(req, blocking=True, timeout=1)


@pytest.mark.usefixtures('easy_client')
class TestSystemClient(object):

    def test_blocking(self):
        sys_client = setup_system_client(
            system_name='sleeper', timeout=1)

        req = sys_client.sleep(amount=0)
        assert req.status == 'SUCCESS'

        with pytest.raises(TimeoutExceededError):
            sys_client.sleep(amount=2)

    def test_non_blocking(self):
        sys_client = setup_system_client(
            system_name='sleeper', blocking=False, timeout=1)

        future = sys_client.sleep(amount=0)
        assert future.result().status == 'SUCCESS'

        with pytest.raises(TimeoutExceededError):
            sys_client.sleep(amount=2).result()
