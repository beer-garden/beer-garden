import importlib
import sys

from brewtils import AutoDecorator, Plugin


def main():
    module_name = sys.argv[1]
    class_name = sys.argv[2]

    passedArgs = []
    passedKwargs = {}
    if len(sys.argv) > 3:
        for arg in sys.argv[:3]:
            if "=" in arg:
                passedKwargs[arg.split("=")[0]] = arg.split("=")[1]
            else:
                passedArgs.append(arg)

    module = importlib.import_module(module_name)
    my_class = getattr(module, class_name)

    auto = AutoDecorator()
    auto.updateClientClass(
        my_class,
        name=passedKwargs.get("NAME", None),
        version=passedKwargs.get("VERSION", None),
    )

    my_class_initialized = my_class(*passedArgs)

    plugin = Plugin(
        name=my_class_initialized._bg_name,
        version=my_class_initialized._bg_version,
        client=my_class_initialized,
    )

    plugin.run()


if __name__ == "__main__":
    main()
