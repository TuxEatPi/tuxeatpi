"""
Thie module contains basic and useful classes
to create Tux component like wings, eyes, ...
"""

import logging
import threading
import time

# Use fake GPIO
import GPIOSim.RPi.in_mem as GPIO


from tuxeatpi.libs.common import AbstractComponent, threaded, subprocessed, capability, can_transmit
from tuxeatpi.settings import SettingsError
from tuxeatpi.libs.lang import gtt


__all__ = ["threaded",
           "subprocessed",
           "capability",
           "can_transmit",
           "Shape",
           "BaseComponent",
           ]


class Shape(AbstractComponent, threading.Thread):
    """Class define a TuxDroid Shape"""

    def __init__(self, settings, fake=False):
        threading.Thread.__init__(self)
        AbstractComponent.__init__(self)
        self.logger.info("Body starting with shape: %s", self._name)
        self._settings = settings
        self.fake = fake

    def _get_logger(self):
        self.logger = logging.getLogger(name="tep").getChild("body")

    def help_(self):
        """Return shape help"""
        return gtt("Use my body")

    def _load_components(self):
        """Load all shape components like wings, head, ..."""
        raise NotImplementedError

    def run(self):
        """Default run loop for aptitude"""
        # Load body components
        self._load_components()
        # Run default loop
        AbstractComponent.run(self)


class BaseComponent(AbstractComponent, threading.Thread):  # pylint: disable=R0903
    """Parent class use for component like wings, eyes, ...

    Define some checks about component creation and
    switches function for handle input events
    """
    pins = None

    def __init__(self, pins):
        threading.Thread.__init__(self)
        AbstractComponent.__init__(self)
        # Set logger
        self.logger.info("Body Component starting %s", self._name)
        # Check pin_name_list validity
        if not isinstance(self.pins, dict):
            raise SettingsError("Bad attribute definition: pins must be a dict")
        for pin_name in self.pins.keys():
            if not isinstance(pin_name, str):
                raise SettingsError("Bad item definition in pin_name_list {}", pin_name)
        # Check pins validity
        if not isinstance(pins, dict):
            raise SettingsError("Bad attribute definition: pins")
        if set(pins.keys()) != set(self.pins.keys()):
            raise SettingsError("Your pin list should be {} for component {}",
                                self.pins.keys(), self.__class__.__name__)

        # Set pins
        self.pins = pins

    def help_(self):
        """Help about the aptitude"""
        raise NotImplementedError

    def _get_logger(self):
        self.logger = logging.getLogger(name="tep").getChild("body").getChild(self._name)

    def _switch(self, event_pin_id):
        """Add event to Tux event queue"""
        # Get pin_name
        event_name = event_pin_id
        for pin_name, pin_id in self.pins.items():
            if pin_id == event_pin_id:
                # Get pin name and remove 'pin_' prefix
                event_name = pin_name

        if event_name == event_pin_id:
            # It seems we got an event on a pin which is not registered
            # This should be impossible
            self.logger.warning("New event on pin {}, but the pin doesn't seems register on this "
                                "component: {}".format(event_pin_id, self.__class__.__name__))
        else:
            # Create event
            event = Event(component=self.__class__.__name__, name=event_name, pin_id=event_pin_id)
            self.logger.info("New event: %s", event)
            # self.event_queue.put(event)


def push_switch(pin_id):
    """Simulate switch pushing"""
    GPIO.set_pin_value(pin_id, 0)
    time.sleep(0.1)
    GPIO.set_pin_value(pin_id, 1)


class Event(object):  # pylint: disable=R0903
    """Event are created for each input event
    And store in Tux event queue
    """
    def __init__(self, component, name, pin_id):
        self.component = component
        self.name = name
        self.pin_id = pin_id

    def __repr__(self):
        return '<Event: %(component)s - %(name)s on pin %(pin_id)s>' % self.__dict__
