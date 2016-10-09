"""
Thie module contains basic and useful classes
to create Tux component like wings, eyes, ...
"""

import logging
from queue import Queue, Empty
import threading
import time

# Use fake GPIO
import GPIOSim.RPi.in_mem as GPIO

import functools


class Shape(threading.Thread):

    def __init__(self, settings, fake):
        threading.Thread.__init__(self)
        self._name = self.__class__.__name__
        self._settings = settings
        self.fake = fake
        self.logger = logging.getLogger(name="tep").getChild("body")
        self.logger.info("Body starting with shape: %s", self._name)
        self._must_run = True
        self.answer_queue = {}
        self.task_queue = Queue()
        self.answer_event_dict = {}
        self._must_run = True


    def _load_components(self):
        raise NotImplementedError

    def push_answer(self, tmn):
        """Push an transmission answert to the current aptitude"""
        if tmn.id_ not in self.answer_event_dict:
            self.logger.warning("Transmission `%s` NOT found in answer event dict", tmn.id_)
            return
        self.answer_queue[tmn.id_] = tmn
        self.answer_event_dict[tmn.id_].set()

    def push_transmission(self, task):
        """Push a transmission to the current aptitute"""
        self.task_queue.put(task)

    def create_transmission(self, s_func, mod, func, params):
        """Create a new transmission and push it to the brain"""
        tmn = create_transmission(self.__class__.__name__,
                                  s_func,
                                  mod, func, params)
        return tmn

    def wait_for_answer(self, tmn_id, timeout=5):
        """Blocking wait for a transmission answer on the current aptitude"""
        self.logger.info("Creating waiting event for transmission: %s", tmn_id)
        self.answer_event_dict[tmn_id] = multiprocessing.Event()
        self.logger.info("Waiting for transmission: %s", tmn_id)
        ret = self.answer_event_dict[tmn_id].wait(timeout)
        if ret is False:
            # or critical ?
            self.logger.warning("No answer received for transmission: %s", tmn_id)
            # No answer
            return None
        else:
            self.answer_event_dict.pop(tmn_id)
            answer = self.answer_queue.pop(tmn_id)
            return answer

    def stop(self):
        """Stop The current Aptitude"""
        self.logger.info("Stopping")
        self._must_run = False

    def run(self):
        """Default run loop for aptitude"""
        self.logger.info("Starting")
        # Load body components
        self._load_components()
        while self._must_run:
            try:
                task = self.task_queue.get(timeout=1)
            except Empty:
                continue
            method_names = task.func.split(".")
            method = self
            for method_name in method_names:
                print("obj %s" % method)
                print("method_name %s" % method_name)
                method = getattr(method, method_name)
                if method is None:
                    self.logger.critical("No body func found %s", task.func)
            method(**task.content['attributes'])


class BaseComponent(object):  # pylint: disable=R0903
    """Parent class use for component like wings, eyes, ...

    Define some checks about component creation and
    switches function for handle input events
    """
    pins = None

    def __init__(self, pins):
        self._name = self.__class__.__name__
        # Set logger
        self.logger = logging.getLogger(name="tep").getChild("body").getChild(self._name)
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
