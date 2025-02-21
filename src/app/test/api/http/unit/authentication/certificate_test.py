import pytest
from box import Box
from mock import patch
from tornado.httputil import HTTPServerRequest

from beer_garden import config
from beer_garden.api.http.authentication.login_handlers.certificate import (
    CertificateLoginHandler,
)


@pytest.fixture(autouse=True)
def app_config_certificate(monkeypatch):
    app_config = Box(
        {
            "auth": {
                "enabled": True,
                "authentication_handlers": {
                    "certificate": {
                        "enabled": True,
                        "create_users": True,
                    }
                },
            },
        }
    )
    monkeypatch.setattr(config, "_CONFIG", app_config)
    yield app_config


@pytest.fixture
def app_config_certificate_create_users_false(monkeypatch, app_config_certificate):
    pointer = app_config_certificate.auth.authentication_handlers.certificate
    pointer.create_users = False
    monkeypatch.setattr(config, "_CONFIG", app_config_certificate)

    yield app_config_certificate


@pytest.fixture(autouse=True)
def valid_certificate():
    return {
        "subject": ((("commonName", "user1"),), (("organizationName", "client"),)),
        "issuer": (
            (("commonName", "TLSGenSelfSignedtRootCA"),),
            (("localityName", "$$$$"),),
        ),
        "version": 3,
        "serialNumber": "02",
        "notBefore": "Oct  6 12:46:30 2020 GMT",
        "notAfter": "Oct  4 12:46:30 2030 GMT",
        "subjectAltName": (
            ("DNS", "localhost"),
            ("DNS", "localhost"),
            ("DNS", "localhost"),
            ("DNS", "beer-garden"),
            ("DNS", "prometheus"),
            ("DNS", "grafana"),
            ("DNS", "rabbitmq"),
        ),
    }


class TestCertificateLoginHandler:
    @patch("tornado.httputil.HTTPServerRequest.get_ssl_certificate")
    def test_user_login_create_user_false(
        self,
        mock_certificate,
        valid_certificate,
        app_config_certificate_create_users_false,
    ):
        mock_certificate.return_value = valid_certificate
        handler = CertificateLoginHandler()

        request = HTTPServerRequest()
        authenticated_user = handler.get_user(request)

        assert authenticated_user is None

    @patch("tornado.httputil.HTTPServerRequest.get_ssl_certificate")
    def test_user_login_create_user(self, mock_certificate, valid_certificate):
        mock_certificate.return_value = valid_certificate
        handler = CertificateLoginHandler()

        request = HTTPServerRequest()
        authenticated_user = handler.get_user(request)

        assert authenticated_user is not None
        assert authenticated_user.username == "user1"

    @patch("tornado.httputil.HTTPServerRequest.get_ssl_certificate")
    def test_user_login_existing_user(
        self,
        mock_certificate,
        valid_certificate,
        app_config_certificate_create_users_false,
    ):
        mock_certificate.return_value = valid_certificate
        handler = CertificateLoginHandler()

        request = HTTPServerRequest()
        authenticated_user = handler.get_user(request)

        assert authenticated_user is not None
        assert authenticated_user.username == "user1"