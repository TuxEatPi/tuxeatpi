from io import StringIO
from multiprocessing import Queue
import logging
import sys
import time
import unittest

from tuxeatpi.actionner.actionner import Actionner
from tuxeatpi.tux import Tux
from tuxeatpi.libs.settings import Settings


class ActionnerTests(unittest.TestCase):

    def test_actionner(self):
        """Basic Actionner Tests"""
        logger = logging.getLogger(name="TestLogger")
        conf_file = "tests/actionner/conf/actionner_tests_conf_1.yaml"
        mytux = Tux(conf_file)
        # Get actionner object
        actionner = mytux.actionner
        # Test mute functions
#        self.assertEqual(voice.is_mute(), False, "Bad mute state")
#        voice.mute()
#        self.assertEqual(voice.is_mute(), True, "Bad mute state")
#        voice.unmute()
#        self.assertEqual(voice.is_mute(), False, "Bad mute state")
        # Test speaking
#        self.assertEqual(voice.is_speaking(), False, "Bad speaking state")
        # Test tts
        mytux.actionner._say("hello world")
        time.sleep(2)
#        self.assertRaises(RuntimeError, lambda: tts_queue.put("hello world"))
        mytux.shutdown()
