import json
import time
import re

from brewtils import get_easy_client, load_config, SystemClient
from brewtils.errors import ValidationError, SaveError
from brewtils.models import PatchOperation
from urllib3.exceptions import TimeoutError


COMPLETED_STATUSES = ['SUCCESS', 'ERROR', 'CANCELED']
CONFIG = None
PLUGIN_MAP = {
    'complex': {'running': False},
    'dynamic': {'running': False},
    'echo': {'running': False},
    'error': {'running': False},
    'sleeper': {'running': False}
}


class RequestGenerator(object):

    def __init__(self, **kwargs):
        self.default_system = kwargs.get('system', None)
        self.default_system_version = kwargs.get('system_version', None)
        self.default_command = kwargs.get('command', None)
        self.default_parameters = kwargs.get('parameters', {})
        self.default_comment = kwargs.get('comment', None)
        self.default_instance_name = kwargs.get('instance_name', None)

    @staticmethod
    def get_or_raise(d, key, default=None, required=True):
        value = d.get(key, default)
        if value is None and required:
            raise ValueError("No %s was specified. Cannot generate request." % key)
        return value

    def generate_request(self, **kwargs):
        system = self.get_or_raise(kwargs, 'system', default=self.default_system)
        system_version = self.get_or_raise(kwargs, 'system_version', default=self.default_system_version)
        command = self.get_or_raise(kwargs, 'command', default=self.default_command)
        comment = kwargs.get('comment', self.default_comment)
        instance_name = self.get_or_raise(kwargs, 'instance_name', default=self.default_instance_name)
        parameters = self.get_or_raise(kwargs, 'parameters', default=self.default_parameters)

        return {
            "system": system,
            "system_version": system_version,
            "command": command,
            "comment": comment,
            "instance_name": instance_name,
            "parameters": parameters
        }


def wait_for_in_progress(client, request, timeout=1, max_delay=1):
    """Generate a request and wait for that request to be marked as IN_PROGRESS

    Will throw a ValueError if it misses the window (i.e. a request goes to a completed state
    and we never saw it IN_PROGRESS)

    :param client:
    :param request:
    :param timeout:
    :param max_delay:
    :return:
    """
    request = client.create_request(request)
    delay_time = 0.01
    total_wait_time = 0
    while request.status != 'IN_PROGRESS':

        if request.status in COMPLETED_STATUSES:
            raise ValueError("Error waiting for request to go to in progress. Status %s" % request.status)

        if timeout and total_wait_time > timeout:
            raise TimeoutError("Timed out waiting for request to go to IN_PROGRESS")

        time.sleep(delay_time)
        total_wait_time += delay_time
        delay_time = min(delay_time * 2, max_delay)

        request = client.find_unique_request(id=request.id)

    return request


def wait_for_response(client, request, timeout=1, max_delay=1):
    request = client.create_request(request)
    delay_time = 0.01
    total_wait_time = 0
    while request.status not in COMPLETED_STATUSES:

        if timeout and total_wait_time > timeout:
            raise TimeoutError("Timed out waiting for request to complete")

        time.sleep(delay_time)
        total_wait_time += delay_time
        delay_time = min(delay_time * 2, max_delay)

        request = client.find_unique_request(id=request.id)

    return request


def delete_plugins(client, name_regex="test"):
    systems = client.find_systems()
    for system in systems:
        if re.match(name_regex, system.name):
            stop_system(client, system)
            delete_system(client, system.id)


def delete_system(client, system_id):
    client._remove_system_by_id(system_id)


def stop_system(client, system, timeout=1, max_delay=1):
    for instance in system.instances:
        stop_instance(client, instance, timeout, max_delay)


def stop_instance(client, instance, timeout=15, max_delay=1):
    instance = client.update_instance_status(instance.id, 'STOPPED')

    delay_time = 0.01
    total_wait_time = 0
    while instance.status not in ['DEAD', 'STOPPED', 'UNRESPONSIVE']:

        if timeout and total_wait_time > timeout:
            raise TimeoutError("Timed out waiting for instance to stop")

        time.sleep(delay_time)
        total_wait_time += delay_time
        delay_time = min(delay_time * 2, max_delay)

        instance = get_instance(client, instance.id)

    return instance


def get_instance(client, instance_id):

    return client.get_instance(instance_id)


def get_config():
    global CONFIG

    if CONFIG is None:
        # import os
        # cwd = os.getcwd()
        # raise Exception("Path = " + cwd)
        try:
            with open('rest/config.json') as config_file:
                file_config = json.load(config_file)
        except Exception:
            file_config = {}

        CONFIG = load_config(**file_config)

    return CONFIG


def wait_for_connection(client, timeout=30, max_delay=5):
    connected = False
    delay_time = 0.1
    total_wait_time = 0

    while not connected:
        try:
            client.get_version()
            connected = True
        except Exception:
            if total_wait_time > timeout:
                raise TimeoutError("Timed out waiting to connect to beer-garden.")

            time.sleep(delay_time)
            total_wait_time += delay_time
            delay_time = min(delay_time * 2, max_delay)


def wait_for_plugins(client, timeout=30, max_delay=5):
    for plugin_name, plugin_info in PLUGIN_MAP.items():
        if not plugin_info['running']:
            delay_time = 0.1
            total_wait_time = 0

            while not plugin_info['running']:
                system = client.find_unique_system(name=plugin_name,
                                                   version=plugin_info.get("version"))

                is_running = True
                if system and system.instances:
                    for instance in system.instances:
                        if instance.status != 'RUNNING':
                            is_running = False
                            break
                PLUGIN_MAP[plugin_name]['running'] = is_running

                if is_running:
                    plugin_info['running'] = True
                else:
                    if total_wait_time > timeout:
                        raise TimeoutError("Timed out waiting to connect to beer-garden.")

                    time.sleep(delay_time)
                    total_wait_time += delay_time
                    delay_time = min(delay_time * 2, max_delay)


def setup_easy_client():
    client = get_easy_client(**get_config())
    wait_for_connection(client)
    wait_for_plugins(client)

    return client


def setup_system_client(**kwargs):
    client_args = kwargs.copy()
    client_args.update(get_config())
    client = SystemClient(**client_args)

    wait_for_connection(client._easy_client)
    wait_for_plugins(client._easy_client)

    return client
