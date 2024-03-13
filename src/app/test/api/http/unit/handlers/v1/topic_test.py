# -*- coding: utf-8 -*-
import json

import beer_garden.events
import beer_garden.router
import pytest
from beer_garden.db.mongo.models import Role, RoleAssignment, User, Topic, Subscriber
import beer_garden.api.http.handlers.v1.garden
from beer_garden.api.http.authentication import issue_token_pair
from beer_garden.topic import create_topic
from brewtils.models import Topic as BrewtilsTopic
from brewtils.models import Subscriber as BrewtilsSubscriber
from tornado.httpclient import HTTPError, HTTPRequest


@pytest.fixture(autouse=True)
def topic_permitted():
    topic = Topic(name="sometopic").save()

    yield topic
    topic.delete()


@pytest.fixture(autouse=True)
def topic_not_permitted():
    topic = Topic(name="remotetopic").save()

    yield topic
    topic.delete()


@pytest.fixture
def subscriber():
    return Subscriber(
        garden="bg",
        namespace="beer-garden",
        system="system",
        version="0.0.1",
        instance="inst",
        command="command",
    )


class TestTopicAPI:
    @pytest.mark.gen_test
    def test_get_topic(self, http_client, base_url, topic_permitted):
        url = f"{base_url}/api/v1/topics/{topic_permitted.id}"

        response = yield http_client.fetch(url)
        response_body = json.loads(response.body.decode("utf-8"))
        print(response_body)

        assert response.code == 200
        assert response_body["id"] == str(topic_permitted.id)

    @pytest.mark.gen_test
    def test_delete_topic(
        self,
        http_client,
        base_url,
        topic_permitted,
    ):
        url = f"{base_url}/api/v1/topics/{topic_permitted.id}"
        headers = {}

        request = HTTPRequest(url, method="DELETE", headers=headers)
        response = yield http_client.fetch(request)

        assert response.code == 204
        assert len(Topic.objects.filter(id=topic_permitted.id)) == 0

    @pytest.mark.gen_test
    def test_patch_topic(
        self,
        http_client,
        base_url,
        topic_permitted,
        subscriber
    ):
        url = f"{base_url}/api/v1/topics/{topic_permitted.id}"
        headers = {
            "Content-Type": "application/json",
        }

        patch_body = [{"operation": "add", "value": str(subscriber)}]
        request = HTTPRequest(
            url, method="PATCH", headers=headers, body=json.dumps(patch_body)
        )
        response = yield http_client.fetch(request)

        assert response.code == 200
        assert len(Topic.objects.get(id=topic_permitted.id).subscribers) == 1
        assert Topic.objects.get(id=topic_permitted.id).subscribers[0] == subscriber


class TestTopicListAPI:
    @pytest.mark.gen_test
    def test_get_all_topics(self, http_client, base_url):
        url = f"{base_url}/api/v1/topics"

        response = yield http_client.fetch(url)
        response_body = json.loads(response.body.decode("utf-8"))

        assert response.code == 200
        assert len(response_body) == 2

    @pytest.mark.gen_test
    def test_post_topic(
        self,
        http_client,
        base_url,
    ):
        url = f"{base_url}/api/v1/topics"
        headers = {}

        post_body = {
            "name": "newtopic",
            "subscribers": [
                {
                    "garden": "mygarden",
                }
            ],
        }
        request = HTTPRequest(
            url, method="POST", headers=headers, body=json.dumps(post_body)
        )
        response = yield http_client.fetch(request)

        assert response.code == 201
        assert len(Topic.objects.filter(name="newtopic")) == 1
