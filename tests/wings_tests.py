import unittest
import time
import logging
from threading import Thread

try:
    from RPi import GPIO
except RuntimeError:
    # Use fake GPIO
    from GPIOSim.RPi import GPIO


from tests.utils import set_pin_value
from tuxeatpi.tux import Tux
from tuxeatpi.components.wings import Wings


class WingsMover(Thread):

    def __init__(self, position_pin):
        Thread.__init__(self)
        self.position_pin = position_pin

    def stop(self):
        self.running = False

    def run(self):
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

    def __init__(self, pins, event_queue ,logger):
        self.move_wings_thread = WingsMover(pins.get('position'))
        Wings.__init__(self, pins, event_queue ,logger)

    def move_start(self):
        self.move_wings_thread = WingsMover(self.pins.get('position'))
        self.move_wings_thread.start()

    def move_stop(self):
        self.move_wings_thread.stop()

    def push_wing(self, side):
        push_switch(GPIO.GPIO_TO_PIN[self.pins[side + '_switch']])

def push_switch(pin_id):
    set_pin_value(pin_id, 0)
    time.sleep(0.1)
    set_pin_value(pin_id, 1)


class Test(unittest.TestCase):

    def setUp(self):
        GPIO.init()
        # Start GPIO eventer
        self.eventer = GPIO.Eventer()
        self.eventer.start()

    def tearDown(self):
        self.eventer.stop()

    def test_wings1(self):
        mytux = Tux('pingu', log_level=logging.DEBUG)
        mytux.wings = WingsTest(mytux.wings.pins, mytux.wings.event_queue, mytux.wings.logger)
        # Test calibrate
        time.sleep(3)
        self.assertEqual(mytux.wings.get_position(), "down")

        # Move up
        mytux.wings.move_up()
        time.sleep(2)
        self.assertEqual(mytux.wings.get_position(), "up")
        # Move down
        mytux.wings.move_down()
        time.sleep(2)
        self.assertEqual(mytux.wings.get_position(), "down")
        # Move 5 times
        mytux.wings.move_count(5)
        time.sleep(5)
        self.assertEqual(mytux.wings.get_position(), "up")

    def test_wings2(self):
        mytux = Tux('pingu', log_level=logging.DEBUG)
        mytux.wings = WingsTest(mytux.wings.pins, mytux.wings.event_queue, mytux.wings.logger)
        # Test calibrate
        time.sleep(3)
        self.assertEqual(mytux.wings.get_position(), "down")

        # test left switch event
        mytux.wings.push_wing('left')
        event = mytux.event_queue.get(timeout=5)
        self.assertEqual(event.component, 'WingsTest')
        self.assertEqual(event.pin_id, mytux.wings.pins.get('left_switch'))
        self.assertEqual(event.name, 'left_switch')

        # test left switch event
        mytux.wings.push_wing('right')
        event = mytux.event_queue.get(timeout=5)
        self.assertEqual(event.component, 'WingsTest')
        self.assertEqual(event.pin_id, mytux.wings.pins.get('right_switch'))
        self.assertEqual(event.name, 'right_switch')

    def test_wings3(self):
        mytux = Tux('pingu', log_level=logging.DEBUG)
        mytux.wings = WingsTest(mytux.wings.pins, mytux.wings.event_queue, mytux.wings.logger)
        # Test calibrate
        time.sleep(3)
        self.assertEqual(mytux.wings.get_position(), "down")
        mytux.wings.move_count(3)
        time.sleep(3)
        self.assertEqual(mytux.wings.get_position(), "up")
        mytux.wings.move_count(2)
        time.sleep(2)
        self.assertEqual(mytux.wings.get_position(), "up")
