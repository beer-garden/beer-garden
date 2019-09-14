# -*- coding: utf-8 -*-
import copy
import json

import datetime
from mock import Mock, patch

from beer_garden.bg_utils.mongo.models import RefreshToken
from .. import TestHandlerBase


class TokenAPITest(TestHandlerBase):
    def setUp(self):
        self.refresh_dict = {
            "issued": datetime.datetime.utcnow(),
            "expires": datetime.datetime.utcnow() + datetime.timedelta(days=1),
            "payload": {"sub": "USER_ID_HERE"},
        }

        db_dict = copy.deepcopy(self.refresh_dict)
        self.refresh = RefreshToken(**db_dict)

        super(TokenAPITest, self).setUp()

    def tearDown(self):
        RefreshToken.objects.delete()

    def test_old_refresh(self):
        self.refresh.save()
        response = self.fetch("/api/v1/tokens/" + str(self.refresh.id))
        self.assertEqual(200, response.code)
        data = json.loads(response.body.decode("utf-8"))
        assert "token" in data

    def test_old_refresh_not_found(self):
        response = self.fetch("/api/v1/tokens/" + "222222222222222222222222")
        self.assertEqual(403, response.code)

    def test_old_delete(self):
        self.refresh.save()
        response = self.fetch("/api/v1/tokens/" + str(self.refresh.id), method="DELETE")
        self.assertEqual(204, response.code)

    @patch("brew_view.base_handler.BaseHandler.get_secure_cookie")
    def test_get_no_refresh_token(self, get_cookie_mock):
        get_cookie_mock.return_value = None
        response = self.fetch("/api/v1/tokens")
        self.assertEqual(403, response.code)

    @patch("brew_view.base_handler.BaseHandler.get_secure_cookie")
    def test_get_invalid_request_body(self, get_cookie_mock):
        get_cookie_mock.return_value = None
        response = self.fetch(
            "/api/v1/tokens",
            method="GET",
            body="some garbage here.",
            headers={"content-type": "application/json"},
            allow_nonstandard_methods=True,
        )
        self.assertEqual(403, response.code)

    @patch("brew_view.base_handler.BaseHandler.get_secure_cookie")
    def test_get_invalid_refresh_cookie(self, get_cookie_mock):
        get_cookie_mock.return_value = Mock(
            decode=Mock(return_value="222222222222222222222222")
        )
        response = self.fetch("/api/v1/tokens")
        self.assertEqual(403, response.code)

    @patch("brew_view.base_handler.BaseHandler.get_secure_cookie")
    def test_get_refresh_token_expired(self, get_cookie_mock):
        self.refresh.expires = datetime.datetime.utcnow() - datetime.timedelta(days=1)
        self.refresh.save()
        get_cookie_mock.return_value = Mock(decode=Mock(return_value=self.refresh.id))
        response = self.fetch("/api/v1/tokens")
        self.assertEqual(403, response.code)

    @patch("brew_view.base_handler.BaseHandler.get_secure_cookie")
    def test_get_refresh_token_cookie(self, get_cookie_mock):
        self.refresh.save()
        get_cookie_mock.return_value = Mock(decode=Mock(return_value=self.refresh.id))
        response = self.fetch("/api/v1/tokens")
        self.assertEqual(200, response.code)
        data = json.loads(response.body.decode("utf-8"))
        assert "token" in data

    @patch("brew_view.base_handler.BaseHandler.get_secure_cookie")
    def test_get_refresh_token_header(self, get_cookie_mock):
        self.refresh.save()
        get_cookie_mock.return_value = None
        response = self.fetch(
            "/api/v1/tokens",
            method="GET",
            headers={
                "content-type": "application/json",
                "X-BG-RefreshID": str(self.refresh.id),
            },
            allow_nonstandard_methods=True,
        )
        self.assertEqual(200, response.code)
        data = json.loads(response.body.decode("utf-8"))
        assert "token" in data

    def test_patch_noop(self):
        body = "[]"
        response = self.fetch(
            "/api/v1/tokens",
            method="PATCH",
            body=body,
            headers={"content-type": "application/json"},
        )
        self.assertEqual(200, response.code)
        data = json.loads(response.body.decode("utf-8"))
        self.assertEqual(data, None)

    def test_patch_bad_operation(self):
        self.refresh.save()
        body = json.dumps(
            {
                "operations": [
                    {
                        "operation": "INVALID",
                        "path": "/payload",
                        "value": str(self.refresh.id),
                    }
                ]
            }
        )
        response = self.fetch(
            "/api/v1/tokens",
            method="PATCH",
            body=body,
            headers={"content-type": "application/json"},
        )
        self.assertEqual(400, response.code)

    def test_patch_bad_path(self):
        self.refresh.save()
        body = json.dumps(
            {
                "operations": [
                    {
                        "operation": "refresh",
                        "path": "/INVALID",
                        "value": str(self.refresh.id),
                    }
                ]
            }
        )
        response = self.fetch(
            "/api/v1/tokens",
            method="PATCH",
            body=body,
            headers={"content-type": "application/json"},
        )
        self.assertEqual(400, response.code)

    def test_patch_with_value(self):
        self.refresh.save()
        body = json.dumps(
            {
                "operations": [
                    {
                        "operation": "refresh",
                        "path": "/payload",
                        "value": str(self.refresh.id),
                    }
                ]
            }
        )
        response = self.fetch(
            "/api/v1/tokens",
            method="PATCH",
            body=body,
            headers={"content-type": "application/json"},
        )
        self.assertEqual(200, response.code)
        data = json.loads(response.body.decode("utf-8"))
        assert "token" in data

    def test_delete_no_token(self):
        response = self.fetch("/api/v1/tokens", method="DELETE")
        self.assertEqual(403, response.code)

    @patch("brew_view.base_handler.BaseHandler.get_secure_cookie")
    def test_delete_cookie(self, get_cookie_mock):
        self.refresh.save()
        get_cookie_mock.return_value = Mock(
            decode=Mock(return_value=str(self.refresh.id))
        )
        response = self.fetch("/api/v1/tokens", method="DELETE")
        self.assertEqual(204, response.code)
        self.assertEqual(RefreshToken.objects.count(), 0)
