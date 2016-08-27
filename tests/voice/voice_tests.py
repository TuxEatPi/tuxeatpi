from io import StringIO
from multiprocessing import Queue
import logging
import sys
import time
import unittest

try:
    from RPi import GPIO
except RuntimeError:
    # Use fake GPIO
    from GPIOSim.RPi import GPIO

from tuxeatpi.voice.voice import Voice
from tuxeatpi.libs.settings import Settings


class VoiceTests(unittest.TestCase):

    def test_voice(self):
        """Basic Voice Tests"""
        logger = logging.getLogger(name="TestLogger")
        conf_file = "tests/voice/conf/voice_tests_conf_1.yaml"
        tts_queue = Queue()
        settings = Settings(conf_file, logger)
        # Get voice object
        voice = Voice(settings, tts_queue, logger)
        voice.start()
        # Test mute functions
        self.assertEqual(voice.is_mute(), False, "Bad mute state")
        voice.mute()
        self.assertEqual(voice.is_mute(), True, "Bad mute state")
        voice.unmute()
        self.assertEqual(voice.is_mute(), False, "Bad mute state")
        # Test speaking
        self.assertEqual(voice.is_speaking(), False, "Bad speaking state")
        # Test tts
        tts_queue.put("hello world")
        time.sleep(2)
        voice.stop()
        tts_queue.close()
#        self.assertRaises(RuntimeError, lambda: tts_queue.put("hello world"))
