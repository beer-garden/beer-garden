import logging
import time

from brewtils.decorators import parameter, system


@system
class SleeperClient:
    def __init__(self, number_of_times=1):
        self.logger = logging.getLogger(__name__)
        self.number_of_times = number_of_times or 1

    @parameter(key="amount", type="Float", description="Amount of time (in seconds) to sleep.")
    def sleep(self, amount):
        self.logger.info("In Sleep")
        for i in range(self.number_of_times):
            self.logger.info("About to sleep for %d" % amount)
            time.sleep(amount)
            self.logger.info("I'm Awake!")
        self.logger.info("Done with Sleep!")

    @parameter(key="amount", type="Float", description="Amount of time (in seconds) to sleep before erroring.")
    def sleep_and_error(self, amount):
        self.logger.info("In Sleep")
        for i in range(self.number_of_times):
            self.logger.info("About to sleep for %d" % amount)
            time.sleep(amount)
            self.logger.info("I'm Awake!")
            raise ValueError("Error Occurred after %d time." % amount)