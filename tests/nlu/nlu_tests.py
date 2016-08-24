import unittest

from tuxeatpi.tux import Tux


class NLUTests(unittest.TestCase):
    def disable_test_nlu(self):
        """Basic Tests for nlu Class"""
        conf_file = "tests/nlu/conf/nlu_tests_conf_1.yaml"
        mytux = Tux(conf_file)
        self.assertRaises(ValueError, lambda: mytux.nlu.understand_text("What is your name ?", say_it=True))
