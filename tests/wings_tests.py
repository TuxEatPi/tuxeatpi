import unittest
import logging
from queue import Queue
from threading import Thread
import time

try:
    from RPi import GPIO
except RuntimeError:
    # Use fake GPIO
    from GPIOSim.RPi import GPIO

from tests.utils import set_pin_value, push_switch
from tuxeatpi.tux import Tux
from tuxeatpi.components.wings import Wings


class WingsMover(Thread):

    def __init__(self, position_pin):
        """Thread which simulate wings movement"""
        Thread.__init__(self)
        self.position_pin = position_pin

    def stop(self):
        """Stop moving wings"""
        self.running = False

    def run(self):
        """Start moving wings"""
        # Get pin_id from self.pins
        pin_id = GPIO.GPIO_TO_PIN[self.position_pin]
        self.running = True
        while self.running:
            if self.running:
                set_pin_value(pin_id, 1)
                time.sleep(0.1)
            if self.running:
                set_pin_value(pin_id, 0)
                time.sleep(0.1)
            if self.running:
                set_pin_value(pin_id, 1)
                time.sleep(0.1)
            if self.running:
                set_pin_value(pin_id, 0)
                time.sleep(0.25)


class WingsTest(Wings):
    """Fake wings class"""

    def __init__(self, pins, event_queue ,logger):
        self.move_wings_thread = WingsMover(pins.get('position'))
        Wings.__init__(self, pins, event_queue ,logger)

    def move_start(self):
        """Override move_start function for fake one"""
        self.move_wings_thread = WingsMover(self.pins.get('position'))
        self.move_wings_thread.start()
        try:
            super(WingsTest, self).move_start()
        except Exception:
            pass

    def move_stop(self):
        """Override move_stop function for fake one"""
        self.move_wings_thread.stop()
        super(WingsTest, self).move_stop()

    def push_wing(self, side):
        """Simulation push switch function"""
        push_switch(GPIO.GPIO_TO_PIN[self.pins[side + '_switch']])

class WingsTests(unittest.TestCase):

    def setUp(self):
        """Method called before each test function"""
        GPIO.cleanup()
        GPIO.init()
        # Start GPIO eventer
        self.eventer = GPIO.Eventer()
        self.eventer.start()

    def tearDown(self):
        """Method called after each test function"""
        self.eventer.stop()

    def test_wings(self):
        """Testing basic moving functions"""
        # init wings
        pins = {"left_switch": 17, "right_switch": 4, "position": 25, "movement": 22}
        event_queue = Queue()
        logging.basicConfig()
        logger = logging.getLogger(name="TuxEatPi")
        logger.setLevel(logging.DEBUG)
        wings = WingsTest(pins, event_queue, logger)

        # Test calibrate
        time.sleep(5)
        self.assertEqual(wings.get_position(), "down")

        # Move up
        wings.move_to_position("up")
        time.sleep(2)
        self.assertEqual(wings.get_position(), "up")
        # Move down
        wings.move_to_position("down")
        time.sleep(2)
        self.assertEqual(wings.get_position(), "down")
        # Move 5 times
        wings.move_count(5)
        time.sleep(5)
        self.assertEqual(wings.get_position(), "up")

    def test_wings_moving(self):
        """Testing other moving functions"""
        # init wings
        pins = {"left_switch": 17, "right_switch": 4, "position": 25, "movement": 22}
        event_queue = Queue()
        logging.basicConfig()
        logger = logging.getLogger(name="TuxEatPi")
        logger.setLevel(logging.DEBUG)
        wings = WingsTest(pins, event_queue, logger)
        # Test calibrate
        time.sleep(5)
        self.assertEqual(wings.get_position(), "down")
        # Test count
        wings.move_count(3)
        time.sleep(3)
        self.assertEqual(wings.get_position(), "up")
        wings.move_count(2)
        time.sleep(2)
        self.assertEqual(wings.get_position(), "up")
        # Test moving by time
        wings.move_time(3)
        time.sleep(1)
        self.assertTrue(wings.is_moving)
        time.sleep(3)
        self.assertFalse(wings.is_moving)
        # Bad move
        self.assertRaises(Exception, lambda: wings.move_to_position("bottom"))

    def test_wings_push_switches(self):
        """Testing push switches"""
        # init wings
        pins = {"left_switch": 17, "right_switch": 4, "position": 25, "movement": 22}
        event_queue = Queue()
        logging.basicConfig()
        logger = logging.getLogger(name="TuxEatPi")
        logger.setLevel(logging.DEBUG)
        wings = WingsTest(pins, event_queue, logger)
        # Test calibrate
        time.sleep(5)
        self.assertEqual(wings.get_position(), "down")

        # test left switch event
        wings.push_wing('left')
        event = event_queue.get(timeout=5)
        self.assertEqual(event.component, 'WingsTest')
        self.assertEqual(event.pin_id, wings.pins.get('left_switch'))
        self.assertEqual(event.name, 'left_switch')

        # test left switch event
        wings.push_wing('right')
        event = event_queue.get(timeout=5)
        self.assertEqual(event.component, 'WingsTest')
        self.assertEqual(event.pin_id, wings.pins.get('right_switch'))
        self.assertEqual(event.name, 'right_switch')
