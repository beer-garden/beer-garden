import time

from brewtils.decorators import parameter, system


@system
class SleeperClient:

    def __init__(self, number_of_times=1):
        self.number_of_times = number_of_times or 1

    @parameter(key="amount", type="Float", description="Amount of time to sleep (in seconds)")
    def sleep(self, amount):
        print("In Sleep")
        i = 0
        while i < self.number_of_times:
            print("About to sleep for %d" % amount)
            time.sleep(amount)
            print("I'm Awake!")
            i += 1
        print("Done with Sleep!")
