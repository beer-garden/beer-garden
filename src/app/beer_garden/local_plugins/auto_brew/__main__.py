import importlib
import sys

from brewtils import Plugin
from brewtils import AutoDecorator


def main():
    module_name = sys.argv[1]
    class_name = sys.argv[2]

    module = importlib.import_module(module_name)
    my_class = getattr(module, class_name)

    auto = AutoDecorator()
    auto.updateClientClass(my_class)

    my_class_initialized = my_class()

    plugin = Plugin(
        name=my_class_initialized._bg_name,
        version=my_class_initialized._bg_version,
        client=my_class_initialized,
    )

    plugin.run()


if __name__ == "__main__":
    main()
