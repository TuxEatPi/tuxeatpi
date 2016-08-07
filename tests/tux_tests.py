from io import StringIO
import logging
import sys
import time
import unittest

try:
    from RPi import GPIO
except RuntimeError:
    # Use fake GPIO
    from GPIOSim.RPi import GPIO

from tuxeatpi.tux import Tux


class TuxTests(unittest.TestCase):

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
        GPIO.cleanup()

    def test_tux(self):
        """Basic Tests"""
        mytux = Tux('pingu', log_level=logging.DEBUG)
        # Test uptime
        time.sleep(2)
        uptime = mytux.get_uptime()
        self.assertEqual(uptime.seconds, 2)
        # Test show uptime
        # Save good stdout
        saved_stdout = sys.stdout
        # Override stdout
        out = StringIO()
        sys.stdout = out
        # Show uptime in our custom stdout
        mytux.show_uptime()
        # Reset stdout
        sys.stdout = saved_stdout
        # Get output
        output = out.getvalue().strip()
        self.assertRegexpMatches(output, ", 2 seconds, ")
