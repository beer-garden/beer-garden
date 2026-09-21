# -*- coding: utf-8 -*-
from io import BytesIO

from brewtils.models import Operation, Permissions

from beer_garden.api.http.handlers import AuthorizationHandler


class PluginDeployAPI(AuthorizationHandler):

    async def post(self):
        """
        ---
        summary: Create a Plugin
        parameters:
          - name: plugin_upload
            in: formData
            required: true
            type: file
            description: |
              A compressed file (.zip, .tar.gz, or .tgz) containing a
              plugin to be deployed to the plugin directory
          - name: target_folder
            in: query
            required: false
            type: string
            description: |
              The target directory for the plugin to be deployed to within
              the plugin directory.
          - name: migrate
            in: query
            required: false
            type: boolean
            default: false
            description: |
              If the target directory already exists, should the beer.conf
              be copied into the compressed file content.
        consumes:
          - multipart/form-data
        responses:
          204:
            description: Plugin Successfully Deployed
          400:
            description: Plugin Upload Error
            content:
              text/plain:
                schema:
                  type: 'string'
                example: No Plugin file uploaded
          50x:
            description: Server Exception
            content:
              text/plain:
                schema:
                  type: 'string'
                example: Server Exception
        tags:
            - Files
        """
        self.minimum_permission = Permissions.GARDEN_ADMIN.name
        self.verify_user_global_permission()

        files = self.request.files

        if not files:
            self.set_status(400)
            self.write("No Plugin file uploaded.")
            return

        target_file = self.get_argument("target_file", default=None)
        migrate_arg = self.get_query_argument("migrate", default="false")
        migrate_conf = bool(migrate_arg.lower() == "true")

        if type(files) is dict:
            files = files["plugin_upload"]

        file_info = files[0]
        file_bytes = BytesIO(file_info["body"])
        file_name = file_info["filename"]

        is_zip = file_name.endswith(".zip")
        is_tarfile = file_name.endswith(".tar.gz") or file_name.endswith(".tgz")

        if target_file is None:
            target_file = file_name.split(".")[0]

        await self.process_operation(
            Operation(
                operation_type="PLUGIN_DEPLOY",
                kwargs={
                    "target_folder": target_file,
                    "file_bytes": file_bytes,
                    "migrate_conf": migrate_conf,
                    "is_zip": is_zip,
                    "is_tarfile": is_tarfile,
                },
            ),
        )

        self.set_status(204)
