"""TuxDroid class"""

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
    def __init__(self, name, log_level=logging.WARNING):
        # Set attributes
        self.name = name
        # Voice attributes (Not implemented)
        self.gender = 'Male'
        self.voice = ''
        # Set GPIO mode
        GPIO.setmode(GPIO.BCM)
        # Init queue
        self.event_queue = Queue()
        # Init logging
        logging.basicConfig()
        self.logger = logging.getLogger(name="TuxEatPi")
        self.logger.setLevel(log_level)
        # Create components
        # Create wings
        self.wings_pins = {"left_switch": 17,
                           "right_switch": 4,
                           "position": 25,
                           "movement": 22,
                           }
        self.wings = Wings(self.wings_pins, self.event_queue, self.logger)

    def __del__(self):
        GPIO.cleanup()
