"""Voice component"""

import asyncio
from binascii import unhexlify

import pyaudio

from tuxeatpi.components.base import BaseComponent
from tuxeatpi.libs.voice import do_synthesis


class Voice(BaseComponent):
    """Define voices component

    For now voice use Nuance communications services
    """
    # No pin
    pins = {}

    def __init__(self, settings, event_queue, logger):
        logger.debug("Voice initialization")
        # Maybe the following line is useless ?
        BaseComponent.__init__(self, {}, event_queue, logger)
        # Init private attributes
        self._settings = settings
        self._audio_player = pyaudio.PyAudio()
        self._speaking = False
        self._muted = False

    def __del__(self):
        self._audio_player.terminate()

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
            loop.run_until_complete(do_synthesis(self._settings['speech']['url'] + '/v1',
                                                 self._settings['speech']['app_id'],
                                                 unhexlify(self._settings['speech']['app_key']),
                                                 self._settings['speech']['language'],
                                                 self._settings['speech']['voice'],
                                                 self._settings['speech']['codec'],
                                                 text,
                                                 self._audio_player,
                                                 self.logger,
                                                 ))
            self._speaking = False


class VoicesError(Exception):
    """Base class for voice exceptions"""
    pass
