import os

from bg_utils.local_plugin import LocalPlugin
from brewtils.rest.system_client import SystemClient
from echo_sleeper.client import EchoSleeperClient


def main():
    ssl_enabled = os.getenv('BG_SSL_ENABLED', '').lower() != "false"

    plugin = LocalPlugin(
        EchoSleeperClient(
            SystemClient(os.getenv("BG_WEB_HOST"), os.getenv("BG_WEB_PORT"), 'echo', ssl_enabled=ssl_enabled),
            SystemClient(os.getenv("BG_WEB_HOST"), os.getenv("BG_WEB_PORT"), 'sleeper', ssl_enabled=ssl_enabled)),
        max_concurrent=5)
    plugin.run()


if __name__ == '__main__':
    main()
