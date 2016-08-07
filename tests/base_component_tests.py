import unittest
import queue
import logging
from threading import Thread
import time

try:
    from RPi import GPIO
except RuntimeError:
    # Use fake GPIO
    from GPIOSim.RPi import GPIO

from tuxeatpi.components.base import BaseComponent
from tuxeatpi.error import ConfigError


class BaseComponentTests(unittest.TestCase):

    def test_bad_stuff(self):
        """Testing bad args base component"""
        event_queue = queue.Queue()
        logger = logging.getLogger(name="testlogger")
        class MyGoodComponent(BaseComponent):
            pins = {"button1": 4, "button2": 22} 
        good_pins = {"button1": 4, "button2": 22}
        # Test 1
        class MyBadComponent1(BaseComponent):
            pins = None
        self.assertRaises(ConfigError, lambda: MyBadComponent1(good_pins, event_queue, logger))
        # Test 2
        class MyBadComponent2(BaseComponent):
            pins = {4: 4, 22: 22}
        self.assertRaises(ConfigError, lambda: MyBadComponent2(good_pins, event_queue, logger))
        # Test 3
        bad_pins1 = None
        self.assertRaises(ConfigError, lambda: MyGoodComponent(bad_pins1, event_queue, logger))
        # Test 4
        bad_pins2 = {4: 4, 22: 22}
        self.assertRaises(ConfigError, lambda: MyGoodComponent(bad_pins2, event_queue, logger))
        # Test 5
        bad_pins4 = {"button1": 4, "button2": 9999}
        self.assertRaises(ConfigError, lambda: MyGoodComponent(bad_pins4, event_queue, logger))
        # Test 6
        bad_pins5 = {"button1": 4, "button3": 22}
        self.assertRaises(ConfigError, lambda: MyGoodComponent(bad_pins5, event_queue, logger))
        # Test 7
        bad_pins6 = {"button1": 4, "button2": 4}
        self.assertRaises(ConfigError, lambda: MyGoodComponent(bad_pins6, event_queue, logger))
