from tuxeatpi.body.common import Shape
from tuxeatpi.body.penguin.wings import Wings
from tuxeatpi.body.penguin.fake_wings import FakeWings


try:
    from RPi import GPIO
except (RuntimeError, ImportError):
    # Use fake GPIO
    import GPIOSim.RPi.in_mem as GPIO


class Penguin(Shape):

    def __init__(self, settings, fake):
        Shape.__init__(self, settings, fake)
        self.wings = None

    def _load_components(self):
        # Create components
        if self.fake is False:
            # Create wings
            self.wings = Wings(self._settings, self.event_queue, self.logger)
        else:
            # Create fake wings
            GPIO.init()
            self.eventer = GPIO.Eventer()
            self.eventer.start()
            self.wings = FakeWings(self._settings)
