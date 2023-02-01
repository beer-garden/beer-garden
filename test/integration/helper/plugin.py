import time
from threading import Thread

import helper
from brewtils import system, parameter, Plugin

thread_map = {}


def start_plugin(plugin, client):
    global thread_map
    t = Thread(target=plugin.run)
    t.daemon = True
    t.start()
    t.join(1)
    if t.is_alive():
        thread_map[plugin.unique_name] = {"thread": t, "plugin": plugin}
    else:
        raise Exception("Could not start plugin %s" % plugin.unique_name)
    wait_for_status(client, plugin.instance.id)


def wait_for_status(client, instance_id, timeout=30, max_delay=60):
    instance = helper.get_instance(client, instance_id)
    delay_time = 0.01
    total_wait_time = 0
    while instance.status not in ["RUNNING", "STOPPED", "DEAD"]:
        time.sleep(delay_time)
        if timeout and total_wait_time > timeout:
            raise Exception("Timed out waiting for instance to start")

        time.sleep(delay_time)
        total_wait_time += delay_time
        delay_time = min(delay_time * 2, max_delay)

        instance = helper.get_instance(client, instance.id)

    return instance


def stop_plugin(plugin):
    if plugin.unique_name in thread_map:
        p = thread_map[plugin.unique_name]["plugin"]
        t = thread_map[plugin.unique_name]["thread"]
        p._stop()
        t.join(2)
        if t.is_alive():
            raise Exception("Could not stop plugin: %s" % plugin.unique_name)


class Thread_Plugin(Plugin):
    @staticmethod
    def _set_signal_handlers():
        pass


def create_plugin(name, version, clazz, **kwargs):
    config = helper.get_config()

    # Brewtils 3.2.0ish has a bug that breaks when reusing the same client class
    # It's been fixed in brewtils, but fix it here so we can run tests on that version
    # See https://github.com/beer-garden/beer-garden/issues/1014
    if hasattr(clazz, "current_request"):
        delattr(clazz, "current_request")
    if hasattr(clazz, "_current_request"):
        delattr(clazz, "_current_request")

    return Thread_Plugin(
        client=clazz(),
        name=name,
        version=version,
        bg_host=config.bg_host,
        bg_port=config.bg_port,
        ssl_enabled=config.ssl_enabled,
        **kwargs
    )


@system
class TestPluginV1(object):
    @parameter(key="x", type="Integer")
    @parameter(key="y", type="Integer")
    def add(self, x, y):
        """Add"""
        return x + y


@system
class TestPluginV2(object):
    @parameter(key="x", type="Integer")
    @parameter(key="y", type="Integer")
    def add(self, x, y):
        """Add"""
        return x + y

    @parameter(key="x", type="Integer")
    @parameter(key="y", type="Integer")
    def subtract(self, x, y):
        """Add"""
        return x - y


@system
class TestPluginV1BetterDescriptions(object):
    @parameter(key="x", type="Integer", description="X, which represents an integer")
    @parameter(
        key="y", type="Integer", description="Y, will be added to X (also an integer)"
    )
    def add(self, x, y):
        """Add two numbers together, this description is much better"""
        return x + y
