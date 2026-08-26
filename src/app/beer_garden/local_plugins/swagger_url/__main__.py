import importlib
import sys

from brewtils import SwaggerDecorator, Plugin


def main():

    swaggerUrl = sys.argv[1]
    baseUrl = None
    
    if len(sys.argv) > 2:
        baseUrl = sys.argv[2]

    passedKwargs = {}
    if len(sys.argv) > 3:
        for arg in sys.argv[3:]:
            if "=" in arg:
                passedKwargs[arg.split("=")[0]] = arg.split("=")[1]

    swaggerClient = SwaggerDecorator(swagger_url=swaggerUrl, base_url=baseUrl, name=passedKwargs.pop("NAME", None), version=passedKwargs.pop("VERSION", None),)

    plugin = Plugin(
        name=swaggerClient._bg_name,
        version=swaggerClient._bg_version,
        client=swaggerClient,
    )

    plugin.run()


if __name__ == "__main__":
    main()
