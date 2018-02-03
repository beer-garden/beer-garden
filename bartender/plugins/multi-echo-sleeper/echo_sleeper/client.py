from brewtils.decorators import system, parameter
from echo_sleeper.config import DEFAULT_MESSAGE


@system
class EchoSleeperClient:
    """A multithreaded client that delegates to the Echo and Multi-Sleeper plugins"""

    def __init__(self, echo_client, sleeper_client):
        self.echo_client = echo_client
        self.sleeper_client = sleeper_client

    @parameter(key="message", description="The Message to be Echoed", optional=True, type="String",
               default=DEFAULT_MESSAGE)
    @parameter(key="loud", description="Determines if Exclamation marks are added", optional=True, type="Boolean",
               default=False)
    @parameter(key="amount", description="How long to sleep", optional=True, type="Integer", default=10)
    def say_sleep(self, message=DEFAULT_MESSAGE, loud=False, amount=10):
        """Echos using Echo and sleeps using Multi-Sleeper"""

        echo_request = self.echo_client.say(message=message, loud=loud)
        sleep_request = self.sleeper_client.sleep(amount=amount)

        if echo_request.status != 'SUCCESS':
            self.logger.error("Echo plugin returned with non-success status")
            raise RuntimeError(echo_request.output)

        if sleep_request.status != 'SUCCESS':
            self.logger.error("Sleeper plugin returned with non-success status")
            raise RuntimeError(sleep_request.output)

        return echo_request.output
