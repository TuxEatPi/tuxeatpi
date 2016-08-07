"""
Thie module contains basic and useful classes
to create Tux component like wings, eyes, ...
"""

from tuxeatpi.error import ConfigError


PIN_IDS = [4, 17, 22, 25]


class BaseComponent(object):  # pylint: disable=R0903
    """Parent class use for component like wings, eyes, ...

    Define some checks about component creation and
    switches function for handle input events
    """
    pins = None

    def __init__(self, pins, event_queue, logger):
        # Check pin_name_list validity
        if not isinstance(self.pins, dict):
            raise ConfigError("Bad attribute definition: pins must be a dict")
        for pin_name, pin_id in self.pins.items():
            if not isinstance(pin_name, str):
                raise ConfigError("Bad item definition in pin_name_list {}", pin_name)
        # Check pins validity
        if not isinstance(pins, dict):
            raise ConfigError("Bad attribute definition: pins")
        for pin_name, pin_id in pins.items():
            if not isinstance(pin_name, str):
                raise ConfigError("Bad attribute definition: pins")
            if pin_id not in PIN_IDS:
                raise ConfigError("Bad pin id for pin {}. Should be in {}", pin_name, PIN_IDS)
        if set(pins.keys()) != set(self.pins.keys()):
            raise ConfigError("Your pin list should be {} for component {}",
                              self.pins.keys(), self.__class__.__name__)
        for pin_name1 in self.pins.keys():
            for pin_name2 in self.pins.keys():
                if pin_name1 != pin_name2 and pins[pin_name1] == pins[pin_name2]:
                    raise ConfigError("Bad pin definition: {} and {} are on the same "
                                      "pin id", pin_name1, pin_name2)
        # Set pins
        self.pins = pins
        # Set Event queue
        self.event_queue = event_queue
        # Set logger
        self.logger = logger

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
            self.event_queue.put(event)


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
