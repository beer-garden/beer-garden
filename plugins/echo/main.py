from bg_utils.local_plugin import LocalPlugin
from echo.client import EchoClient


def main():
    plugin = LocalPlugin(EchoClient())
    plugin.run()


if __name__ == '__main__':
    main()
