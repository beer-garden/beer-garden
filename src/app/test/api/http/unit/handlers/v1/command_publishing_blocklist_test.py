import json

import pytest
from tornado.httpclient import HTTPError, HTTPRequest

from beer_garden.db.mongo.models import CommandPublishingBlockList


@pytest.fixture
def blocklist():
    blocklist = CommandPublishingBlockList(
        namespace="garden", system="system", command="command"
    )
    blocklist.save()

    yield blocklist
    blocklist.delete()


class TestCommandPublishingBlockListAPI:
    @pytest.mark.gen_test
    def test_get(self, http_client, base_url, blocklist):
        url = f"{base_url}/api/v1/commandpublishingblocklist/"

        request = HTTPRequest(
            url,
            method="GET",
        )

        response = yield http_client.fetch(request)
        assert response.code == 200

        response_blocklist = json.loads(response.body.decode("utf-8"))[
            "command_publishing_block_list"
        ]
        assert response_blocklist[0]["id"] == str(blocklist.id)

    @pytest.mark.gen_test
    def test_post(self, http_client, base_url):
        url = f"{base_url}/api/v1/commandpublishingblocklist/"

        headers = {"Content-Type": "application/json"}
        body = [{"namespace": "garden", "system": "system", "command": "command"}]
        request = HTTPRequest(
            url, method="POST", headers=headers, body=json.dumps(body)
        )

        response = yield http_client.fetch(request)

        assert response.code == 201
