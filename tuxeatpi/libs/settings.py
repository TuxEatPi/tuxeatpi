"""Settings module can read, check and write configuration file"""

import logging
import os
import yaml


from tuxeatpi.libs.voice import VOICES, CODECS


PIN_IDS = [4, 17, 22, 25]
LEVELS = ('CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG')
GENDERS = ('male', 'female')


class Settings(dict):
    """Class to handle settings: read/check/write"""

    def __init__(self, config_file, logger):
        dict.__init__(self)
        self.config_file = config_file
        self.logger = logger
        self._read_conf()
        # Rewrite it to get the right format
        self.save()

    def _read_conf(self):
        """Read Tux configuration from yaml file
        And set config values
        """
        # Read file
        raw_conf = {}
        if not os.path.isfile(self.config_file):
            raise SettingsError("Bad config file: {}".format(self.config_file))
        with open(self.config_file) as fconf:
            try:
                raw_conf = yaml.load(fconf)
            except yaml.scanner.ScannerError as exp:
                raise SettingsError("Yaml: {}", exp)
        # Check if 'tux' is in configuration
        if "tux" not in raw_conf:
            raise SettingsError("Root key of configuration file should be 'tux'")
        # Save entire configuration
        self.full_config = raw_conf
        # Set values
        for key, value in raw_conf['tux'].items():
            self[key] = value
        # Check conf
        self._check_conf()

    def _check_conf(self):
        """Check settings validity"""
        # Check main keys
        for key in ['global', 'advanced', 'pins', 'speech']:
            if key not in self:
                raise SettingsError("Missing {} key".format(key))
        # Check sections
        self._check_global()
        self._check_advanced()
        self._check_speech()
        self._check_pins()

    def _check_global(self):
        """Check global section"""
        # Check key existences
        self._check_missing_keys('global', ('name', 'gender'))
        # Check values
        self._check_str('global', 'name')
        self._check_choice('global', 'gender', GENDERS)

    def _check_advanced(self):
        """Check advanced section"""
        # Check key existences
        self._check_missing_keys('advanced', ('fake', 'log_level'))
        # Check values
        self._check_bool('advanced', 'fake')
        self._check_choice('advanced', 'log_level', LEVELS)
        # Set logging level
        self.logger.setLevel(getattr(logging, self['advanced']['log_level'].upper()))

    def _check_speech(self):
        """Check speech section"""
        # Check key existences
        self._check_missing_keys('speech', ('language', 'voice', 'codec',
                                            'app_id', 'app_key', 'url'))
        self._check_choice('speech', 'language', VOICES.keys())
        self._check_choice('speech', 'voice', VOICES[self['speech']['language']])
        self._check_choice('speech', 'codec', CODECS)
        self._check_str('speech', 'app_id')
        self._check_str('speech', 'app_key')
        self._check_str('speech', 'url')

    def _check_pins(self):
        """Check pin configuration validity"""
        pin_id_list = []
        if not isinstance(self['pins'], dict):
            raise SettingsError("Bad pins configuration")
        for component_name, component_pins in self['pins'].items():
            if not isinstance(component_pins, dict):
                raise SettingsError("Bad pins component {} configuration", component_name)
            for pin_name, pin_id in component_pins.items():
                if not isinstance(pin_name, str):
                    raise SettingsError("Bad pin name {}:{}", component_name, pin_name)
                elif pin_id not in PIN_IDS:
                    raise SettingsError("Bad pin id for pin {}:{}. Should be in {}",
                                        component_name, pin_name, PIN_IDS)
                elif pin_id in pin_id_list:
                    raise SettingsError("Bad pin definition: {} is used at least twice", pin_id)
                pin_id_list.append(pin_id)

    # Check value functions
    def _check_bool(self, section, name):
        """Check if the setting value is a boolean"""
        if not isinstance(self[section][name], bool):
            raise SettingsError("{}:{} should be True or False".format(section, name))

    def _check_str(self, section, name):
        """Check if the setting value is a string"""
        if not isinstance(self[section][name], str) or self[section][name] == '':
            raise SettingsError("{}:{} can NOT be empty".format(section, name))

    def _check_choice(self, section, name, choices):
        """Check if the setting value is on of the given choices"""
        if self[section][name] not in choices:
            raise SettingsError("{}:{} must be in {} ".format(section, name, ", ".join(choices)))

    def _check_missing_keys(self, section, keys):
        """Check if the setting key exists"""
        for key in keys:
            if key not in self[section]:
                raise SettingsError("Missing {} key in {} section".format(key, section))

    def save(self):
        """Save settings on disk"""
        self._check_conf()
        self.full_config["tux"] = dict(self)
        with open(self.config_file, "w") as fconfig:
            yaml.dump(self.full_config, fconfig, default_flow_style=False, indent=4)


class SettingsError(Exception):
    """Base class for configuration exceptions"""
    pass
