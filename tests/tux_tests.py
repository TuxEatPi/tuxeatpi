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
from tuxeatpi.error import ConfigError


class TuxTests(unittest.TestCase):

    def setUp(self):
        """Method called before each test function"""
        GPIO.cleanup()
        GPIO.init()

    def tearDown(self):
        """Method called after each test function"""
        GPIO.cleanup()

    def test_tux(self):
        """Basic Tests for Tux Class"""
        conf_file = "tests/conf/tux_tests_conf_1.yaml"
        mytux = Tux(conf_file)
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

    def test_bad_conf(self):
        """Bad configuration for Tux class"""
        # Yaml not valid
        conf_file = "tests/conf/tux_tests_conf_2.yaml"
        self.assertRaises(ConfigError, lambda: Tux(conf_file))
        # Missing tux key
        conf_file = "tests/conf/tux_tests_conf_3.yaml"
        self.assertRaises(ConfigError, lambda: Tux(conf_file))
        # Missing main key
        conf_file = "tests/conf/tux_tests_conf_4.yaml"
        self.assertRaises(ConfigError, lambda: Tux(conf_file))
        # Bad loglevel
        conf_file = "tests/conf/tux_tests_conf_5.yaml"
        self.assertRaises(ConfigError, lambda: Tux(conf_file))
        # Missing is not a dict
        conf_file = "tests/conf/tux_tests_conf_6.yaml"
        self.assertRaises(ConfigError, lambda: Tux(conf_file))
        # Bad component pins config
        conf_file = "tests/conf/tux_tests_conf_7.yaml"
        self.assertRaises(ConfigError, lambda: Tux(conf_file))
        # Bad component pin name
        conf_file = "tests/conf/tux_tests_conf_8.yaml"
        self.assertRaises(ConfigError, lambda: Tux(conf_file))
        # Bad pin id
        conf_file = "tests/conf/tux_tests_conf_9.yaml"
        self.assertRaises(ConfigError, lambda: Tux(conf_file))
        # Pin used twice
        conf_file = "tests/conf/tux_tests_conf_10.yaml"
        self.assertRaises(ConfigError, lambda: Tux(conf_file))
        # Bad component key names
        conf_file = "tests/conf/tux_tests_conf_11.yaml"
        self.assertRaises(ConfigError, lambda: Tux(conf_file))
