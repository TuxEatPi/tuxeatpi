"""
TuxDroid class
"""

import logging
from queue import Queue


from tuxeatpi.components.wings import Wings


class Tux(object):  # pylint: disable=R0903
    """Tux droid new life class"""
    def __init__(self, log_level=logging.WARNING):
        self.event_queue = Queue()
        logging.basicConfig()
        self.logger = logging.getLogger(name="TuxEatPi")
        self.logger.setLevel(log_level)
        self.wings_pins = {"left_switch": 4,
                           "right_switch": 17,
                           "position": 22,
                           "movement": 25,
                           }
        self.wings = Wings(self.wings_pins, self.event_queue, self.logger)
