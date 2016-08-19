"""Voice component"""

import asyncio
import binascii

import pyaudio

from tuxeatpi.components.base import BaseComponent
from tuxeatpi.libs.voice import do_synthesis, VOICES
from tuxeatpi.error import ConfigError


class Voice(BaseComponent):
    """Define voices component

    For now voice use Nuance communications services
    """
    # No pin
    pins = {}

    def __init__(self, voice_conf, event_queue, logger):
        logger.debug("Voice initialization")
        # Maybe the following line is useless ?
        BaseComponent.__init__(self, {}, event_queue, logger)

        # Init attributes
        self.language = None
        self.voice = None
        self.use_speex = None
        self.use_opus = None
        self.app_id = None
        self.app_key = None
        self.url = None
        # Init private attributes
        self._audio_player = pyaudio.PyAudio()
        self._speaking = False
        self._muted = False
        # Check config and set attributes
        self._check_config(voice_conf)

    def __del__(self):
        self._audio_player.terminate()

    def _check_config(self, voice_conf):
        """Check voice configuration and set object attributes"""
        #  Check and Set attributes
        for attr in ('language', 'voice', 'speex', 'opus', 'app_id', 'app_key', 'url'):
            if attr not in voice_conf:
                raise ConfigError("Missing {} key in voice section".format(attr))
            setattr(self, attr, voice_conf[attr])
        # Check lang
        if voice_conf.get('language') not in VOICES:
            raise ConfigError("Bad language. Must be:{}".format(VOICES.keys()))
        elif voice_conf.get('voice') not in VOICES[voice_conf.get('language')]:
            raise ConfigError("Bad voice. Must be:{}".format(VOICES[voice_conf.get('language')]))

    def is_mute(self):
        """Return the mute state"""
        return self._muted

    def mute(self):
        """Mute the tux"""
        self._muted = True

    def unmute(self):
        """Unmute the the"""
        self._muted = False

    def is_speaking(self):
        """Check if the tux is currently speaking"""
        return self._speaking

    def tts(self, text):
        """Text to speach"""
        if not self._muted:
            loop = asyncio.get_event_loop()
            self._speaking = True
            # TODO: try/except
            loop.run_until_complete(do_synthesis(self.url + '/v1',
                                                 self.app_id,
                                                 binascii.unhexlify(self.app_key),
                                                 self.language,
                                                 self.voice,
                                                 text,
                                                 self._audio_player,
                                                 self.logger,
                                                 self.use_speex,
                                                 self.use_opus,
                                                 ))
            self._speaking = False


class VoicesError(Exception):
    """Base class for voice exceptions"""
    pass
