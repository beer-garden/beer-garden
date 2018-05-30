import json

from passlib.apps import custom_app_context

from bg_utils.models import Principal
from bg_utils.parser import BeerGardenSchemaParser
from brew_view.base_handler import BaseHandler


class UserAPI(BaseHandler):

    def get(self, user_id):
        """
        ---
        summary: Retrieve a specific User
        parameters:
          - name: user_id
            in: path
            required: true
            description: The ID of the User
            type: string
        responses:
          200:
            description: User with the given ID
            schema:
              $ref: '#/definitions/User'
          404:
            $ref: '#/definitions/404Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Users
        """
        principal = Principal.objects.get(id=str(user_id))

        self.write(BeerGardenSchemaParser.serialize_principal(principal))


class UsersAPI(BaseHandler):

    def post(self):
        """
        ---
        summary: Create a new User
        parameters:
          - name: user
            in: body
            description: The User definition
            schema:
              $ref: '#/definitions/User'
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
        parsed = json.loads(self.request.decoded_body)

        hash = custom_app_context.hash(parsed['password'])

        user = Principal(username=parsed['username'], hash=hash)
        user.save()
