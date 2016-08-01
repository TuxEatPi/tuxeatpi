import unittest

from tuxeatpi.tux import Tux

class TemplateK8s(unittest.TestCase):
    def test_wings_up():
        mytux = Tux()
        mytux.wings.move_up()
        self.assertEqual(mytux.wings.get_position(), "up")
