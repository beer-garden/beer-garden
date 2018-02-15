import os
from concurrent.futures import wait

from brewtils import get_bg_connection_parameters
from brewtils.decorators import system, parameter
from brewtils.rest.system_client import SystemClient

DEFAULT_MESSAGE = "Happy World!"


@system
class EchoSleeperClient:
    """A client that delegates to the Echo and Sleeper plugins"""

    def __init__(self):
        params = get_bg_connection_parameters()

        self.echo_client = SystemClient(system_name='echo', **params)
        self.sleeper_client = SystemClient(system_name='sleeper', **params)
        self.multi_sleeper_client = SystemClient(system_name='multi-sleeper', **params)
        self.error_client = SystemClient(system_name='error', **params)

    @parameter(key="message", description="The message", optional=True, type="String",
               default=DEFAULT_MESSAGE)
    @parameter(key="loud", description="Add exclamation marks", optional=True, type="Boolean",
               default=False)
    @parameter(key="amount", description="How long to sleep", optional=True, type="Float",
               default=10)
    def say_sleep(self, message=DEFAULT_MESSAGE, loud=False, amount=10):
        """Echos using Echo and sleeps using Sleeper"""

        echo_request = self.echo_client.say(message=message, loud=loud)
        self.sleeper_client.sleep(amount=amount)

        return echo_request.output

    @parameter(key="message", description="The message", optional=True, type="String",
               default=DEFAULT_MESSAGE)
    @parameter(key="loud", description="Add exclamation marks", optional=True, type="Boolean",
               default=False)
    def say_error_and_catch(self, message=DEFAULT_MESSAGE, loud=False):
        """Echos using Echo and then errors using Error"""
        echo_request = self.echo_client.say(message=message, loud=loud)
        error_request = self.error_client.string_error_message()

        if error_request.status == "ERROR":
            print("Message errored, but thats ok.")

        return {"echo_output": echo_request.output, "error_output": error_request.output}

    @parameter(key="message", description="The message", optional=True, type="String",
               default=DEFAULT_MESSAGE)
    @parameter(key="loud", description="Add exclamation marks", optional=True, type="Boolean",
               default=False)
    def say_error_and_raise(self, message=DEFAULT_MESSAGE, loud=False):
        """Echos using Echo and then errors using Error"""
        self.echo_client.say(message=message, loud=loud)
        error_request = self.error_client.string_error_message()

        if error_request.status == "ERROR":
            # Note: Don't raise an error this way. You should figure out a way not to use eval.
            raise eval(error_request.error_class)(error_request.output)

    @parameter(key="message", description="The message", optional=True, type="String",
               default=DEFAULT_MESSAGE)
    @parameter(key="loud", description="Add exclamation marks", optional=True, type="Boolean",
               default=False)
    @parameter(key="amount", description="How long to sleep", optional=True, type="Float",
               default=10)
    def sleep_say(self, message=DEFAULT_MESSAGE, loud=False, amount=10):
        """Echos using Echo and sleeps using Sleeper"""

        self.sleeper_client.sleep(amount=amount)

        return self.echo_client.say(message=message, loud=loud).output

    @parameter(key="message", description="The message", optional=True, type="String",
               default=DEFAULT_MESSAGE)
    @parameter(key="loud", description="Add exclamation marks", optional=True, type="Boolean",
               default=False)
    @parameter(key="amount", description="How long to sleep", optional=True, type="Float",
               default=10)
    @parameter(key="number", description="Number of times to sleep", optional=True, type="Integer",
               default=1)
    def super_sleeper(self, message=DEFAULT_MESSAGE, loud=False, amount=10, number=1):
        """Echos using Echo and sleeps using Sleeper"""

        [self.sleeper_client.sleep(amount=amount) for _ in range(number)]

        return self.echo_client.say(message=message, loud=loud).output

    @parameter(key="message", description="The message", optional=True, type="String",
               default=DEFAULT_MESSAGE)
    @parameter(key="loud", description="Add exclamation marks", optional=True, type="Boolean",
               default=False)
    @parameter(key="amount", description="How long to sleep", optional=True, type="Float",
               default=10)
    @parameter(key="number", description="Number of times to sleep", optional=True, type="Integer",
               default=1)
    def super_sleeper_concurrent(self, message=DEFAULT_MESSAGE, loud=False, amount=10, number=1):
        """Echos using Echo and sleeps using Multi-Sleeper"""

        # System client with blocking=False will return Futures
        sleeps = [self.multi_sleeper_client.sleep(amount=amount, _comment=number)
                  for number in range(number)]

        # Wait for all the futures to complete
        wait(sleeps)

        return self.echo_client.say(message=message, loud=loud).output
