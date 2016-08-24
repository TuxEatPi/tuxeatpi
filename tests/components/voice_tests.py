from io import StringIO
from queue import Queue
import logging
import sys
import time
import unittest

try:
    from RPi import GPIO
except RuntimeError:
    # Use fake GPIO
    from GPIOSim.RPi import GPIO

from tuxeatpi.components.voice import Voice
from tuxeatpi.libs.settings import Settings


class VoiceTests(unittest.TestCase):

    def test_tux(self):
        """Basic Tests for Tux Class"""
        logger = logging.getLogger(name="TestLogger")
        conf_file = "tests/components/conf/voice_tests_conf_1.yaml"
        event_queue = Queue()
        settings = Settings(conf_file, logger)
        # Get voice object
        voice = Voice(settings, event_queue, logger)
        # Test mute functions
        self.assertEqual(voice.is_mute(), False, "Bad mute state")
        voice.mute()
        self.assertEqual(voice.is_mute(), True, "Bad mute state")
        voice.unmute()
        self.assertEqual(voice.is_mute(), False, "Bad mute state")
        # Test speaking
        self.assertEqual(voice.is_speaking(), False, "Bad speaking state")
        # Test tts
        self.assertRaises(ValueError, lambda: voice.tts("hello world"))
