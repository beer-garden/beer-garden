from echo_sleeper.client import EchoSleeperClient

from bg_utils.local_plugin import LocalPlugin


if __name__ == '__main__':
    LocalPlugin(EchoSleeperClient()).run()
