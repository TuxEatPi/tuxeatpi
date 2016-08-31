"""TuxDroid class"""

import copy
from datetime import timedelta, datetime
import logging
import queue
import time
import multiprocessing

try:
    from RPi import GPIO
except RuntimeError:
    # Use fake GPIO
    import GPIOSim.RPi.in_mem as GPIO

from tuxeatpi.components.wings import Wings
from tuxeatpi.voice.voice import Voice
from tuxeatpi.actionner.actionner import Actionner
from tuxeatpi.nlu.nlu import NLU
from tuxeatpi.hotword.hotword import HotWord
from tuxeatpi.fake_components.wings import FakeWings
from tuxeatpi.libs.settings import Settings, SettingsError


class Tux(object):
    """Tux droid new life class"""
    def __init__(self, config_file):
        # Init logging
        logging.basicConfig()

        self.logger = logging.getLogger(name="TuxEatPi")
        # Get settings
        self.settings = Settings(config_file, self.logger)

        # Set start time
        self.logger.debug("Starting TuxDroid named '%s'", self.settings['global']['name'])
        self.start_time = time.time()
        # Set GPIO mode
        GPIO.setmode(GPIO.BCM)
        # Init queues
        self.event_queue = queue.Queue()
        self.tts_queue = multiprocessing.Queue()
        self.nlu_queue = multiprocessing.Queue()
        self.action_queue = multiprocessing.Queue()
        # Create components
        if self.settings['advanced']['fake'] is False:
            # Create wings
            self.wings = Wings(self.settings, self.event_queue, self.logger)
        else:
            # Create fake wings
            GPIO.init()
            self.eventer = GPIO.Eventer()
            self.eventer.start()
            self.wings = FakeWings(self.settings,  # pylint: disable=R0204
                                   self.event_queue,
                                   self.logger)

        # hotword
        self.hotword = HotWord(self.settings, self.tts_queue, self.logger)
        self.hotword.start()
        # Init action
        self.actionner = Actionner(self)
        self.actionner.start()
        # Init voice
        self.voice = Voice(self.settings, self.tts_queue, self.logger)
        self.voice.start()
        # Init nlu
        self.nlu = NLU(self.settings, self.action_queue, self.nlu_queue,
                       self.tts_queue, self.logger)
        self.nlu.start()
        # Birth
        self._birth()

    def shutdown(self):
        """Shutdown all processes"""
        self.tts_queue.close()
        self.nlu_queue.close()
        self.action_queue.close()
        if hasattr(self, 'eventer'):
            self.eventer.stop()
        if hasattr(self, 'voice'):
            self.voice.stop()
        if hasattr(self, 'nlu'):
            self.nlu.stop()
        if hasattr(self, 'actionner'):
            self.actionner.stop()
        if hasattr(self, 'hotword'):
            self.hotword.stop()
        GPIO.cleanup()

    def _birth(self):
        """Save the first start timestamp to get the birthday"""
        if 'birthday' not in self.settings['data']:
            self.logger.info('This is a birth of a new TuxDroid')
            self.settings['data']['birthday'] = time.time()
            self.settings.save()
        else:
            self.logger.info('This TuxDroid is already born')

    def say(self, text):
        """Say text

        Add text to the tts queue,
        it will be processed by the voice object
        """
        self.logger.debug("Add %s to tts queue", text)
        self.tts_queue.put(text)

    def understand_text(self, text, say_it=False):
        """Try to understand text

        Add text to the nlu queue,
        it will be processed by the nlu object
        """
        self.logger.debug("Add say_it=%s - %s to nlu queue", say_it, text)
        self.nlu_queue.put((say_it, text))
        # TODO get answer

    def get_uptime(self):
        """Return current uptime"""
        return timedelta(seconds=time.time() - self.start_time)

    def get_birthday(self):
        """Return the tux birthday"""
        return datetime.fromtimestamp(self.settings['data']['birthday'])

    def get_name(self):
        """Return Tux name"""
        return self.settings['global']['name']

    def update_setting(self, settings):
        """Update settings and save it on disk

        If new settings are bad, old settings are keeped
        and the function returns False

        Otherwise, its returns True and use new ones
        """
        self.logger.debug("Updating settings")
        old_settings = copy.copy(self.settings)
        self.settings.update(settings)
        try:
            self.logger.debug("Update settings OK")
            self.settings.save()
            return True
        except SettingsError:
            self.settings.update(old_settings)
            self.logger.debug("Update settings Failed")
            return False
