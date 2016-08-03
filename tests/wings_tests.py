import unittest
import time
import logging
from threading import Thread

from GPIOSim.RPi import GPIO

from tests.utils import set_pin_value
from tuxeatpi.tux import Tux
from tuxeatpi.components.wings import Wings



class WingsMover(Thread):

    def __init__(self):
        Thread.__init__(self)

    def stop(self):
        self.running = False

    def run(self):
        # Get pin_id from self.pins
        pin_id = 'pin14'
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
        self.move_wings_thread = WingsMover()
        Wings.__init__(self, pins, event_queue ,logger)

    def move_start(self):
        self.move_wings_thread.start()

    def move_stop(self):
        self.move_wings_thread.stop()
        self.move_wings_thread = WingsMover()


class Test(unittest.TestCase):

    def setUp(self):
        # Start GPIO eventer
        self.eventer = GPIO.Eventer()
        self.eventer.start()

    def tearDown(self):
        self.eventer.stop()

    def test_wings(self):
        mytux = Tux(log_level=logging.DEBUG)
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


        # test left switch event
        pin_id = 'pin6'
        set_pin_value(pin_id, 0)
        time.sleep(0.1)
        set_pin_value(pin_id, 1)
        event = mytux.event_queue.get()
        self.assertEqual(event.component, 'WingsTest')
        self.assertEqual(event.pin_id, 4)
        self.assertEqual(event.name, 'left_switch')

