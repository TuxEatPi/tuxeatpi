"""Voice component"""

import asyncio
from binascii import unhexlify

import pyaudio

from tuxeatpi.components.base import BaseComponent
from tuxeatpi.libs.nlu import understand_text
from tuxeatpi.nlu.tux import NLUTux


class NLU(BaseComponent):
    """Define voice component

    For now voice use Nuance communications services
    """
    # No pin
    pins = {}

    def __init__(self, tuxdroid):
        tuxdroid.logger.debug("NLU initialization")
        # Maybe the following line is useless ?
        BaseComponent.__init__(self, {}, tuxdroid.event_queue, tuxdroid.logger)
        # Init private attributes
        self._settings = tuxdroid.settings
        self.say = tuxdroid.voice.tts
        self._audio_player = pyaudio.PyAudio()
        self._speaking = False
        self._muted = False
        # Get all NLU actions
        self.actions = {NLUTux.prefix: NLUTux(tuxdroid)}

    def __del__(self):
        self._audio_player.terminate()

    def misunderstand(self, confidence, text_it=False, say_it=False):
        """bad understanding"""
        # TODO add text_it and say_it
        if confidence < 0.8 and confidence > 0.5:
            msg = "I need a confirmation, Could you repeat please ?"
            self.logger.warning("NLU: misunderstood: {}".format(msg))
            # TODO ask to repeat
        if confidence < 0.5:
            msg = "Sorry, I just don't get it"
            self.logger.warning("NLU: misunderstood: {}".format(msg))
        if say_it is True:
            self.say(msg)
        if text_it is True:
            return msg
            # TODO say it

    def understand_text(self, text, say_it=False):
        """Text to speach"""
        loop = asyncio.get_event_loop()
        self._understanding = True
        # TODO: try/except
        speech_args = self._settings['speech']
        ret = loop.run_until_complete(understand_text(speech_args['url'],
                                                      speech_args['app_id'],
                                                      unhexlify(speech_args['app_key']),
                                                      # context_tag=credentials['context_tag'],
                                                      "master",
                                                      text,
                                                      speech_args['language'],
                                                      self.logger,
                                                      ))
        self._understanding = False
        interpretations = ret.get("nlu_interpretation_results", {}).\
            get("payload", {}).get("interpretations", {})
        # TODO: what about if len(interpretations) > 1 ??
        for interpretation in interpretations:
            intent = interpretation.get("action", {}).get("intent", {})
            self.logger.info("Intent: {}".format(intent.get("value")))
            self.logger.info("Confidence: {}".format(intent.get("confidence")))
            # TODO log arguments
            if intent.get("value") == "NO_MATCH":
                # I don't understand :/
                return self.misunderstand(0, True, say_it)
            elif intent.get("confidence") < 0.8:
                # I'm not sure to undestand :/
                return self.misunderstand(intent.get("confidence"), True, say_it)
            else:
                # Check intent name
                if len(intent.get("value").split("__")) != 2:
                    self.logger.critical("BAD Intent name: {}".format(intent.get("value")))
                    return self.misunderstand(0, True, say_it)
                # Run function with parameters
                key, method = intent.get("value").split("__")
                if key in self.actions and hasattr(self.actions[key], method):
                    # TODO add parameters
                    return getattr(self.actions[key], method)(text_it=True, say_it=say_it)
                else:
                    # Missing function
                    self.logger.warning("NLU: understood but no function registered "
                                        "for {}".format(intent.get("value")))
                    # TODO say: Understood, bu I don't know what do...
                    # Please write to the tuxeatpi Team


class NLUError(Exception):
    """Base class for NLU exceptions"""
    pass
