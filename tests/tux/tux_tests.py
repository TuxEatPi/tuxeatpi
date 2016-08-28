from io import StringIO
import logging
import sys
import time
from datetime import timedelta
import unittest

try:
    from RPi import GPIO
except RuntimeError:
    # Use fake GPIO
    from GPIOSim.RPi import GPIO

from tuxeatpi.tux import Tux
from tuxeatpi.libs.settings import SettingsError


class TuxTests(unittest.TestCase):

    def test_tux(self):
        """Basic Tests for Tux Class"""
        conf_file = "tests/tux/conf/tux_tests_conf_1.yaml"
        start_time = time.time()
        mytux = Tux(conf_file)
        # Test uptime
        uptime = mytux.get_uptime()
        end_time = time.time()
        self.assertEqual(uptime.seconds, int(end_time - start_time), "Bad uptime")
        mytux.shutdown()

    def ftest_bad_conf(self):
        """Bad configuration for Tux class"""
        # Yaml not valid
        conf_file = "tests/conf/tux_tests_conf_2.yaml"
        self.assertRaises(SettingsError, lambda: Tux(conf_file))
        # Missing tux key
        conf_file = "tests/conf/tux_tests_conf_3.yaml"
        self.assertRaises(SettingsError, lambda: Tux(conf_file))
        # Missing main key
        conf_file = "tests/conf/tux_tests_conf_4.yaml"
        self.assertRaises(SettingsError, lambda: Tux(conf_file))
        # Bad loglevel
        conf_file = "tests/conf/tux_tests_conf_5.yaml"
        self.assertRaises(SettingsError, lambda: Tux(conf_file))
        # Missing is not a dict
        conf_file = "tests/conf/tux_tests_conf_6.yaml"
        self.assertRaises(SettingsError, lambda: Tux(conf_file))
        # Bad component pins config
        conf_file = "tests/conf/tux_tests_conf_7.yaml"
        self.assertRaises(SettingsError, lambda: Tux(conf_file))
        # Bad component pin name
        conf_file = "tests/conf/tux_tests_conf_8.yaml"
        self.assertRaises(SettingsError, lambda: Tux(conf_file))
        # Bad pin id
        conf_file = "tests/conf/tux_tests_conf_9.yaml"
        self.assertRaises(SettingsError, lambda: Tux(conf_file))
        # Pin used twice
        conf_file = "tests/conf/tux_tests_conf_10.yaml"
        self.assertRaises(SettingsError, lambda: Tux(conf_file))
        # Bad component key names
        conf_file = "tests/conf/tux_tests_conf_11.yaml"
        self.assertRaises(SettingsError, lambda: Tux(conf_file))
