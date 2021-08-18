from beer_garden.db.mongo.models import User


def create_user(**kwargs) -> User:
    """Creates a User using the provided kwargs. The created user is saved to the
    database and returned.

    Args:
        **kwargs: Keyword arguments accepted by the User __init__

    Returns:
        User: The created User instance
    """
    user = User(**kwargs)

    if user.password:
        user.set_password(user.password)

    user.save()

    return user


def update_user(user: User, **kwargs) -> User:
    """Updates the provided User by setting its attributes to those provided by kwargs.
    The updated user object is then saved to the database and returned.

    Args:
        user: The User instance to be updated
        **kwargs: Keyword arguments corresponding to User model attributes

    Returns:
        User: the updated User instance
    """
    for key, value in kwargs.items():
        if key == "password":
            user.set_password(value)
        else:
            setattr(user, key, value)

    user.save()

    return user
