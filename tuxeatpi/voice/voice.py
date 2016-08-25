"""Voice component"""

import asyncio
from binascii import unhexlify
from queue import Empty
from multiprocessing import Process

from tuxeatpi.voice.common import do_synthesis


class Voice(Process):
    """Define voices component

    For now voice use Nuance communications services
    """
    def __init__(self, settings, tts_queue, logger):
        Process.__init__(self)
        logger.debug("Voice initialization")
        # Set queue
        self.tts_queue = tts_queue
        # Set logger
        self.logger = logger
        # Init private attributes
        self._settings = settings
        self._speaking = False
        self._muted = False
        self._must_run = False

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

    def stop(self):
        """Stop process"""
        self._must_run = False
        self.tts_queue.close()
        self.terminate()

    def run(self):
        """Text to speech"""
        self._must_run = True
        while self._must_run:
            try:
                text = self.tts_queue.get(timeout=1)
            except Empty:
                self.logger.debug("No text received")
                continue
            self.logger.debug("Text received: {}".format(text))
            if not self._muted:
                self._speaking = True
                loop = asyncio.get_event_loop()
                # TODO: try/except
                try:
                    loop.run_until_complete(
                        do_synthesis(self._settings['speech']['url'] + '/v1',
                                     self._settings['speech']['app_id'],
                                     unhexlify(self._settings['speech']['app_key']),
                                     self._settings['speech']['language'],
                                     self._settings['speech']['voice'],
                                     self._settings['speech']['codec'],
                                     text,
                                     self.logger,
                                     ))
                except Exception as exp:  # pylint: disable=W0703
                    self.logger.critical(exp)
                loop.stop()
                self._speaking = False


class VoicesError(Exception):
    """Base class for voice exceptions"""
    pass
