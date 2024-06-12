from brewtils.models import Role as BrewtilsRole
from mongoengine import ValidationError


def validate_permissions(permissions):
    for permission in permissions:
        if permission not in BrewtilsRole.PERMISSION_TYPES:
            raise ValidationError(
                f"{permission} is not a valid permission. All permissions must be "
                "present in Permission."
            )
