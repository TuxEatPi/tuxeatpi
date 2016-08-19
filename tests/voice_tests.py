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


class VoiceTests(unittest.TestCase):

    def test_tux(self):
        """Basic Tests for Tux Class"""
        conf_file = "tests/conf/tux_tests_conf_1.yaml"
        start_time = time.time()
        mytux = Tux(conf_file)
        # Test mute functions
        self.assertEqual(mytux.voice.is_mute(), False, "Bad mute state")
        mytux.voice.mute()
        self.assertEqual(mytux.voice.is_mute(), True, "Bad mute state")
        mytux.voice.unmute()
        self.assertEqual(mytux.voice.is_mute(), False, "Bad mute state")
        # Test speaking
        self.assertEqual(mytux.voice.is_speaking(), False, "Bad speaking state")
        # Test tts
        self.assertRaises(RuntimeError, lambda: mytux.voice.tts("hello world"))

    def test_bad_conf(self):
        """Bad configuration for Voice class"""
        # Missing voice key
        conf_file = "tests/conf/voice_tests_conf_2.yaml"
        self.assertRaises(ConfigError, lambda: Tux(conf_file))
        # Bad language
        conf_file = "tests/conf/voice_tests_conf_3.yaml"
        self.assertRaises(ConfigError, lambda: Tux(conf_file))
        # Bad voice
        conf_file = "tests/conf/voice_tests_conf_4.yaml"
        self.assertRaises(ConfigError, lambda: Tux(conf_file))
