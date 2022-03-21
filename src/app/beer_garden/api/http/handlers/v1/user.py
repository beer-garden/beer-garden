# -*- coding: utf-8 -*-
from brewtils.schemas import UserCreateSchema
from marshmallow import ValidationError

from beer_garden.api.authorization import Permissions
from beer_garden.api.http.exceptions import BadRequest
from beer_garden.api.http.handlers import AuthorizationHandler
from beer_garden.api.http.schemas.v1.user import (
    UserListSchema,
    UserPasswordChangeSchema,
    UserPatchSchema,
    UserSchema,
)
from beer_garden.db.mongo.models import User
from beer_garden.user import create_user, update_user

USER_CREATE = Permissions.USER_CREATE.value
USER_READ = Permissions.USER_READ.value
USER_UPDATE = Permissions.USER_UPDATE.value
USER_DELETE = Permissions.USER_DELETE.value


class UserAPI(AuthorizationHandler):
    def get(self, username):
        """
        ---
        summary: Retrieve a specific User
        parameters:
          - name: username
            in: path
            required: true
            description: The username of the User
            type: string
        responses:
          200:
            description: User with the given username
            schema:
              $ref: '#/definitions/User'
          404:
            $ref: '#/definitions/404Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Users
        """
        user = User.objects.get(username=username)
        response = UserSchema().dump(user).data

        self.write(response)

    def delete(self, username):
        """
        ---
        summary: Delete a specific User
        parameters:
          - name: username
            in: path
            required: true
            description: The username of the User
            type: string
        responses:
          204:
            description: User has been successfully deleted
          404:
            $ref: '#/definitions/404Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Users
        """
        self.verify_user_global_permission(USER_DELETE)

        user = User.objects.get(username=username)
        user.delete()

        self.set_status(204)

    def patch(self, username):
        """
        ---
        summary: Partially update a User
        parameters:
          - name: username
            in: path
            required: true
            description: The username of the User
            type: string
          - name: patch
            in: body
            required: true
            description: |
              A subset of User attributes to update, most commonly the password.
            schema:
              $ref: '#/definitions/UserPatch'
        responses:
          200:
            description: User with the given username
            schema:
              $ref: '#/definitions/User'
          400:
            $ref: '#/definitions/400Error'
          404:
            $ref: '#/definitions/404Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Users
        """
        self.verify_user_global_permission(USER_UPDATE)

        try:
            user_data = (
                UserPatchSchema(strict=True).load(self.request_body, partial=True).data
            )
            db_user = User.objects.get(username=username)
        except (ValidationError, User.DoesNotExist) as exc:
            raise BadRequest(reason=f"{exc}")

        user = update_user(db_user, **user_data)

        response = UserSchema().dump(user).data
        self.write(response)


class UserListAPI(AuthorizationHandler):
    def get(self):
        """
        ---
        summary: Retrieve all Users
        responses:
          200:
            description: All Users
            schema:
              $ref: '#/definitions/UserList'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Users
        """
        users = User.objects.all()
        response = UserListSchema().dump({"users": users}).data

        self.write(response)

    def post(self):
        """
        ---
        summary: Create a new User
        parameters:
          - name: user
            in: body
            description: The user
            schema:
              $ref: '#/definitions/UserCreate'
        consumes:
          - application/json
        responses:
          201:
            description: A new User has been created
            schema:
              $ref: '#/definitions/User'
          400:
            $ref: '#/definitions/400Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Users
        """
        self.verify_user_global_permission(USER_CREATE)

        user_data = UserCreateSchema().load(self.request_body).data
        create_user(**user_data)

        self.set_status(201)


class UserPasswordChangeAPI(AuthorizationHandler):
    def post(self):
        """
        ---
        summary: Allows a user to change their own password
        parameters:
          - name: password_change
            in: body
            description: The current password for verification and the new password
            schema:
              $ref: '#/definitions/UserPasswordChange'
        consumes:
          - application/json
        responses:
          204:
            description: The password has been changed
          400:
            $ref: '#/definitions/400Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Password
        """
        user = self.current_user

        try:
            password_data = (
                UserPasswordChangeSchema(strict=True).load(self.request_body).data
            )
        except ValidationError as exc:
            raise BadRequest(reason=f"{exc}")

        if user.verify_password(password_data["current_password"]):
            user.set_password(password_data["new_password"])
            user.save()
        else:
            raise BadRequest(reason="Current password incorrect")

        self.set_status(204)


class WhoAmIAPI(AuthorizationHandler):
    def get(self):
        """
        ---
        summary: Retrieve requesting User
        responses:
          200:
            description: Requesting User
            schema:
              $ref: '#/definitions/User'
          401:
            $ref: '#/definitions/401Error'
          403:
            $ref: '#/definitions/403Error'
        tags:
          - Users
        """
        user = self.current_user
        response = UserSchema().dump(user).data

        self.write(response)
