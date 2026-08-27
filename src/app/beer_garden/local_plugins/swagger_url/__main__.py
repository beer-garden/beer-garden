import importlib
import sys

from brewtils import Plugin, SwaggerDecorator


def main():

    swaggerUrl = sys.argv[1]

    passedKwargs = {}
    if len(sys.argv) > 2:
        for arg in sys.argv[2:]:
            if "=" in arg:
                passedKwargs[arg.split("=")[0]] = arg.split("=")[1]

    swaggerClient = SwaggerDecorator(
        swagger_url=swaggerUrl,
        base_url=passedKwargs.pop("BASEURL", None),
        name=passedKwargs.pop("NAME", None),
        version=passedKwargs.pop("VERSION", None),
    )

    plugin = Plugin(
        name=swaggerClient._bg_name,
        version=swaggerClient._bg_version,
        description=swaggerClient._bg_description,
        client=swaggerClient,
    )

    plugin.run()


if __name__ == "__main__":
    main()
