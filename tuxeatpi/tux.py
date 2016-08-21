"""TuxDroid class"""

from datetime import timedelta
import logging
from queue import Queue
import time

try:
    from RPi import GPIO
except RuntimeError:
    # Use fake GPIO
    from GPIOSim.RPi import GPIO

from tuxeatpi.components.wings import Wings
from tuxeatpi.components.voice import Voice
from tuxeatpi.fake_components.wings import FakeWings
from tuxeatpi.libs.settings import Settings


class Tux(object):
    """Tux droid new life class"""
    def __init__(self, config_file):
        # Init logging
        logging.basicConfig()
        self.logger = logging.getLogger(name="TuxEatPi")
        # Get settings
        self.settings = Settings(config_file, self.logger)

        # Set start time
        self.logger.debug("Starting TuxDroid named '%s'", self.settings['global']['name'])
        self.start_time = time.time()
        # Set GPIO mode
        GPIO.setmode(GPIO.BCM)
        # Init queue
        self.event_queue = Queue()
        # Create components
        if self.settings['advanced']['fake'] is False:
            # Create wings
            self.wings = Wings(self.settings, self.event_queue, self.logger)
        else:
            # Start fake eventer
            self.eventer = GPIO.Eventer()
            self.eventer.start()
            GPIO.init()
            # Create fake wings
            self.wings = FakeWings(self.settings,  # pylint: disable=R0204
                                   self.event_queue,
                                   self.logger)
        # Init voice
        self.voice = Voice(self.settings, self.event_queue, self.logger)

    def __del__(self):
        if hasattr(self, 'eventer'):
            self.eventer.stop()
        GPIO.cleanup()

    def get_uptime(self):
        """Return current uptime"""
        return timedelta(seconds=time.time() - self.start_time)

    def show_uptime(self):
        """Show current uptime in readable string"""
        ret_str = ", ".join(["{{}} {}".format(data) for data in ["days",
                                                                 "minutes",
                                                                 "seconds",
                                                                 "microseconds"]])
        uptime = self.get_uptime()
        print(ret_str.format(uptime.days,
                             uptime.seconds // 60,
                             uptime.seconds % 60,
                             uptime.microseconds))
