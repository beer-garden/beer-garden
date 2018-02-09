from bg_utils.local_plugin import LocalPlugin
from error.client import ErrorClient


def main():
    plugin = LocalPlugin(ErrorClient())
    plugin.run()


if __name__ == '__main__':
    main()
