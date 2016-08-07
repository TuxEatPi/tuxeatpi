"""TuxDroid class"""

from datetime import timedelta
import logging
from queue import Queue
import time

try:
    from RPi import GPIO
except RuntimeError:
    # Use fake GPIO
    from GPIOSim.RPi import GPIO
    GPIO.init()
import yaml


from tuxeatpi.components.wings import Wings
from tuxeatpi.components.base import PIN_IDS
from tuxeatpi.error import ConfigError


class Tux(object):
    """Tux droid new life class"""
    def __init__(self, config_file):
        # Init attributes
        self.name = None
        self.gender = None
        self.voice = None
        self.log_level = None
        self.pins = {}
        # Read config file
        self.config_file = config_file
        self._read_conf()
        # Set start time
        self.logger.debug("Starting TuxDroid named '%s'", self.name)
        self.start_time = time.time()
        # Voice attributes (Not implemented)
        self.gender = 'Male'
        self.voice = ''
        # Set GPIO mode
        GPIO.setmode(GPIO.BCM)
        # Init queue
        self.event_queue = Queue()
        # Init logging
        # Create components
        # Create wings
        self.wings = Wings(self.pins['wings'], self.event_queue, self.logger)

    def __del__(self):
        GPIO.cleanup()

    def _read_conf(self):
        """Read Tux configuration from yaml file
        And set Tux attributes
        """
        raw_conf = {}
        with open(self.config_file) as fconf:
            try:
                raw_conf = yaml.load(fconf)
            except yaml.scanner.ScannerError as exp:
                raise ConfigError("Yaml: {}", exp)
        # Check if 'tux' is in configuration
        if "tux" not in raw_conf:
            raise ConfigError("Root key of configuration file should be 'tux'")
        # Set attributes
        for attr in ('name', 'gender', 'voice', 'pins', 'log_level'):
            if attr not in raw_conf.get("tux"):
                raise ConfigError("Missing {} key in tux section".format(attr))
            setattr(self, attr, raw_conf["tux"][attr])
        # Set log
        if not hasattr(logging, self.log_level.upper()):
            raise ConfigError("Bad log level configuration configuration")
        logging.basicConfig()
        self.logger = logging.getLogger(name="TuxEatPi")
        self.logger.setLevel(getattr(logging, raw_conf.get("tux", {})['log_level'].upper()))
        # Check pins
        self._check_pins()

    def _check_pins(self):
        """Check pin configuration validity"""
        pin_id_list = []
        if not isinstance(self.pins, dict):
            raise ConfigError("Bad pins configuration")
        for component_name, component_pins in self.pins.items():
            if not isinstance(component_pins, dict):
                raise ConfigError("Bad pins component {} configuration", component_name)
            for pin_name, pin_id in component_pins.items():
                if not isinstance(pin_name, str):
                    raise ConfigError("Bad pin name {}:{}", component_name, pin_name)
                elif pin_id not in PIN_IDS:
                    raise ConfigError("Bad pin id for pin {}:{}. Should be in {}",
                                      component_name, pin_name, PIN_IDS)
                elif pin_id in pin_id_list:
                    raise ConfigError("Bad pin definition: {} is used at least twice", pin_id)
                pin_id_list.append(pin_id)

    def get_uptime(self):
        """Return current uptime"""
        return timedelta(seconds=time.time() - self.start_time)

    def show_uptime(self):
        """Show current uptime in readable string"""
        ret_str = ", ".join(["{{}} {}".format(data) for data in ["days",
                                                                 "minutes",
                                                                 "seconds",
                                                                 "microseconds"]])
        uptime = self.get_uptime()
        print(ret_str.format(uptime.days,
                             uptime.seconds // 60,
                             uptime.seconds % 60,
                             uptime.microseconds))
