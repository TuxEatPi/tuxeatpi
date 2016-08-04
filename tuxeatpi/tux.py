"""
TuxDroid class
"""

import logging
from queue import Queue

try:
    from RPi import GPIO
except RuntimeError:
    # Use fake GPIO
    from GPIOSim.RPi import GPIO
    GPIO.init()


from tuxeatpi.components.wings import Wings


class Tux(object):  # pylint: disable=R0903
    """Tux droid new life class"""
    def __init__(self, log_level=logging.WARNING):
        # Set GPIO mode
        GPIO.setmode(GPIO.BCM)

        self.event_queue = Queue()
        logging.basicConfig()
        self.logger = logging.getLogger(name="TuxEatPi")
        self.logger.setLevel(log_level)
        self.wings_pins = {"left_switch": 17,
                           "right_switch": 25,
                           "position": 4,
                           "movement": 22,
                           }
        self.wings = Wings(self.wings_pins, self.event_queue, self.logger)

    def __del__(self):
        GPIO.cleanup()
