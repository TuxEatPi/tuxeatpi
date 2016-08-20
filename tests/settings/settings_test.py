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

from tuxeatpi.libs.settings import Settings, SettingsError


class SettingsTests(unittest.TestCase):

    def test_bad_conf(self):
        """Bad configuration for Tux class"""
        logger = logging.getLogger(name="TestLogger")
        # No file
        conf_file = "tests/settings/conf/no_file.yaml"
        self.assertRaises(SettingsError, lambda: Settings(conf_file, logger))
        # Config file not a file
        conf_file = "tests/settings/conf"
        self.assertRaises(SettingsError, lambda: Settings(conf_file, logger))
        # Yaml not valid
        conf_file = "tests/settings/conf/settings_tests_conf_1.yaml"
        self.assertRaises(SettingsError, lambda: Settings(conf_file, logger))
        # Missing tux key
        conf_file = "tests/settings/conf/settings_tests_conf_2.yaml"
        self.assertRaises(SettingsError, lambda: Settings(conf_file, logger))
        # Missing main key
        conf_file = "tests/settings/conf/settings_tests_conf_3.yaml"
        self.assertRaises(SettingsError, lambda: Settings(conf_file, logger))
        # Missing global:gender key
        conf_file = "tests/settings/conf/settings_tests_conf_4.yaml"
        self.assertRaises(SettingsError, lambda: Settings(conf_file, logger))
        # Bad global:name
        conf_file = "tests/settings/conf/settings_tests_conf_5.yaml"
        self.assertRaises(SettingsError, lambda: Settings(conf_file, logger))
        # Bad loglevel
        conf_file = "tests/settings/conf/settings_tests_conf_6.yaml"
        self.assertRaises(SettingsError, lambda: Settings(conf_file, logger))
        # Bad speech:speex
        conf_file = "tests/settings/conf/settings_tests_conf_7.yaml"
        self.assertRaises(SettingsError, lambda: Settings(conf_file, logger))
        # Bad component pins config
        conf_file = "tests/settings/conf/settings_tests_conf_8.yaml"
        self.assertRaises(SettingsError, lambda: Settings(conf_file, logger))
        # Bad component pin name
        conf_file = "tests/settings/conf/settings_tests_conf_9.yaml"
        self.assertRaises(SettingsError, lambda: Settings(conf_file, logger))
        # Bad pin id
        conf_file = "tests/settings/conf/settings_tests_conf_10.yaml"
        self.assertRaises(SettingsError, lambda: Settings(conf_file, logger))
        # Pin used twice
        conf_file = "tests/settings/conf/settings_tests_conf_11.yaml"
        self.assertRaises(SettingsError, lambda: Settings(conf_file, logger))
        # Bad pins section
        conf_file = "tests/settings/conf/settings_tests_conf_12.yaml"
        self.assertRaises(SettingsError, lambda: Settings(conf_file, logger))
