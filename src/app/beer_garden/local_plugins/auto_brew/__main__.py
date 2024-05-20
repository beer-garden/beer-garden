import importlib
import sys

from brewtils import AutoDecorator, Plugin


def main():
    module_name = sys.argv[1]
    class_name = sys.argv[2]

    autoArgs = []
    autoKwargs = {}
    passedKwargs = {}
    if len(sys.argv) > 3:
        for arg in sys.argv[3:]:
            if "ARG=" in arg:
                autoArgs.append(arg.split("=")[1])
            elif "KWARG=" in arg:
                autoKwargs[arg.split("=")[1]] = arg.split("=")[2]
            elif "=" in arg:
                passedKwargs[arg.split("=")[0]] = arg.split("=")[1]

    module = importlib.import_module(module_name)
    my_class = getattr(module, class_name)

    auto = AutoDecorator()
    auto.updateClientClass(
        my_class,
        name=passedKwargs.pop("NAME", None),
        version=passedKwargs.pop("VERSION", None),
    )

    my_class_initialized = my_class(*autoArgs, **autoKwargs)

    plugin = Plugin(
        name=my_class_initialized._bg_name,
        version=my_class_initialized._bg_version,
        client=my_class_initialized,
    )

    plugin.run()


if __name__ == "__main__":
    main()
