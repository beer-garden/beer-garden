from mongoengine import ValidationError

from beer_garden.api.authorization import Permissions


def validate_permissions(permissions):
    valid_permissions = [p.value for p in Permissions]

    for permission in permissions:
        if permission not in valid_permissions:
            raise ValidationError(
                f"{permission} is not a valid permission. All permissions must be "
                "present in Permission."
            )
