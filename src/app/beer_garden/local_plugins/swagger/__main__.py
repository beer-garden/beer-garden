import importlib
import sys

from brewtils import SwaggerDecorator, Plugin


def main():

    swaggerPath = sys.argv[1]
    baseUrl = None
    
    if len(sys.argv) > 2:
        baseUrl = sys.argv[2]

    swaggerClient = SwaggerDecorator(swaggerPath, baseUrl)

    plugin = Plugin(
        name=swaggerClient._bg_name,
        version=swaggerClient._bg_version,
        client=swaggerClient,
    )

    plugin.run()


if __name__ == "__main__":
    main()
