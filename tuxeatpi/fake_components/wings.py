"""Fake Wings component"""

from threading import Thread
import time

# Use fake GPIO
import GPIOSim.RPi.in_mem as GPIO


from tuxeatpi.components.wings import Wings
from tuxeatpi.fake_components.base import push_switch


class FakeWings(Wings):
    """Fake wings class"""
    def __init__(self, pins, event_queue, logger):
        self.move_wings_thread = FakeWingsMover(pins.get('position'))
        Wings.__init__(self, pins, event_queue, logger)

    def move_start(self):
        """Override move_start function for fake one"""
        self.move_wings_thread = FakeWingsMover(self.pins.get('position'))
        self.move_wings_thread.start()
        try:
            super(FakeWings, self).move_start()
        except Exception:  # pylint: disable=W0703
            pass

    def move_stop(self):
        """Override move_stop function for fake one"""
        self.move_wings_thread.stop()
        super(FakeWings, self).move_stop()

    def push_wing(self, side):
        """Simulation push switch function"""
        push_switch(GPIO.GPIO_TO_PIN[self.pins[side + '_switch']])


class FakeWingsMover(Thread):
    """Thread which simulate wings movement"""
    # TODO make it stoppable in hug with Ctrl-C signal
    def __init__(self, position_pin):
        Thread.__init__(self)
        self.position_pin = position_pin

    def stop(self):
        """Stop moving wings"""
        self.running = False

    def run(self):
        """Start moving wings"""
        # Get pin_id from self.pins
        pin_id = GPIO.GPIO_TO_PIN[self.position_pin]
        self.running = True
        while self.running:
            if self.running:
                GPIO.set_pin_value(pin_id, 1)
                time.sleep(0.1)
            if self.running:
                GPIO.set_pin_value(pin_id, 0)
                time.sleep(0.1)
            if self.running:
                GPIO.set_pin_value(pin_id, 1)
                time.sleep(0.1)
            if self.running:
                GPIO.set_pin_value(pin_id, 0)
                time.sleep(0.25)
