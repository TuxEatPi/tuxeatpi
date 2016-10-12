"""Penguin shape module"""
from tuxeatpi.body.common import Shape
from tuxeatpi.body.penguin.wings import Wings
from tuxeatpi.body.penguin.fake_wings import FakeWings


try:
    from RPi import GPIO
except (RuntimeError, ImportError):
    # Use fake GPIO
    import GPIOSim.RPi.in_mem as GPIO


class Penguin(Shape):
    """Penguin shape class"""

    def __init__(self, settings, fake):
        Shape.__init__(self, settings, fake)
        self.wings = None
        self._eventer = None

    def _load_components(self):
        """Load all shape components"""
        # Create components
        if self.fake is False:
            # Create wings
            self.wings = Wings(self._settings)
        else:
            # Create fake wings
            GPIO.init()
            self._eventer = GPIO.Eventer()
            self._eventer.start()
            self.wings = FakeWings(self._settings)  # pylint: disable=R0204
        # start components
        self.wings.start()

    def stop(self):
        """Stop the shape"""
        Shape.stop(self)
        self.wings.stop()
        if self._eventer is not None:
            self._eventer.stop()
