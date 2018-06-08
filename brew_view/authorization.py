import base64

import jwt
from mongoengine.errors import DoesNotExist
from passlib.apps import custom_app_context

import brew_view
from bg_utils.models import Principal


def basic_auth(auth_header):
    auth_decoded = base64.b64decode(auth_header[6:]).decode()
    username, password = auth_decoded.split(':')

    # In this case return 403 to prevent an attacker from being able to
    # enumerate a list of user names
    try:
        principal = Principal.objects.get(username=username)

        if custom_app_context.verify(password, principal.hash):
            return principal
    except DoesNotExist:
        pass

    return None


def bearer_auth(auth_header):
    token = auth_header.split(' ')[1]

    decoded = jwt.decode(token,
                         brew_view.tornado_app.settings["cookie_secret"],
                         algorithm='HS256')

    try:
        return Principal.objects.get(id=decoded['sub'])
    except DoesNotExist:
        pass

    return None
