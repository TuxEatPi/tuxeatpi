"""
TuxDroid class
"""

from queue import Queue

from tuxeatpi.components.wings import Wings

class Tux(object):
    """Tux droid new life class"""
    def __init__(self):
        self.event_queue = Queue()
        wings_pins = {"left_switch": 4,
                      "right_switch": 17,
                      "position": 22,
                      "movement": 25,
                     }
        self.wings = Wings(wings_pins, self.event_queue)
