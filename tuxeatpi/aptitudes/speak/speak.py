"""Aptitude module for TuxDroid voice and speech"""

import time
import asyncio
from binascii import unhexlify


from tuxeatpi.aptitudes.common import SubprocessedAptitude, capability, can_transmit
from tuxeatpi.aptitudes.speak.common import VOICES, do_synthesis
from tuxeatpi.libs.lang import gtt


class Speak(SubprocessedAptitude):
    """Text-to-Speech aptitude"""

    def __init__(self, tuxdroid):
        SubprocessedAptitude.__init__(self, tuxdroid)
        self.start_time = time.time()
        self._muted = False
        self._loop = None

    def is_speaking(self):
        """Check if the tux is currently speaking"""
        # TODO should be not working ...
        return self._speaking

    def run(self):
        self._loop = asyncio.get_event_loop()
        SubprocessedAptitude.run(self)
        self._loop.stop()

    def help_(self):
        """Return aptitude help"""
        return gtt("say anything")

    @capability(gtt("Give my mute state"))
    @can_transmit
    def is_mute(self):
        """Return the mute state"""
        return self._muted

    @capability(gtt("Mute myself"))
    @can_transmit
    def mute(self):
        """Mute the tux"""
        self._muted = True

    @capability(gtt("Unmute myself"))
    @can_transmit
    def unmute(self):
        """Unmute the the"""
        self._muted = False

    @capability(gtt("Say something"))
    @can_transmit
    def say(self, tts):
        """Text to speech"""
        # Reload config from file because we are in an other Process
        if not self._muted:
            self.settings.reload()
            lang = self.settings['speech']['language']
            voice = VOICES[lang][self.settings['global']['gender']]
            self.logger.debug("Language: %s", lang)
            self.logger.debug("Voice: %s", voice)
            self.logger.debug("Text received: %s", tts)
            self._speaking = True
            # FIXME sometimes I got an sound error...
            try:
                self._loop.run_until_complete(
                    do_synthesis(self.settings['speech']['url'] + '/v1',
                                 self.settings['speech']['app_id'],
                                 unhexlify(self.settings['speech']['app_key']),
                                 lang,
                                 voice,
                                 self.settings['speech']['codec'],
                                 tts,
                                 self.logger,
                                 ))
            except BaseException as exp:
                self.logger.critical(exp)
                return {"error": str(exp)}
            self._speaking = False
            self.logger.debug("End of speaking")
        else:
            self.logger.debug("Muted - No TTS")
        return {"result": "said"}
