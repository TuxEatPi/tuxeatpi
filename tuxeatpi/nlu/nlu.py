"""Voice component"""

import asyncio
from binascii import unhexlify
from multiprocessing import Process
from queue import Empty

from tuxeatpi.nlu.common import understand_text
from tuxeatpi.libs.lang import gtt


class NLU(Process):
    """Define voice component

    For now NLU use Nuance communications services
    """
    def __init__(self, settings, action_queue, nlu_queue, tts_queue, logger):
        Process.__init__(self)
        logger.debug("NLU initialization")
        # Set queues
        self.nlu_queue = nlu_queue
        self.tts_queue = tts_queue
        self.action_queue = action_queue
        # Set logger
        self.logger = logger
        # Init private attributes
        self._settings = settings
        self._speaking = False
        self._muted = False
        self._must_run = False

    def _say(self, text):
        """Put text in tts queue"""
        self.tts_queue.put(text)

    def _run_action(self, action, method, args, print_it=False, text_it=True, say_it=False):
        """Put action in action queue"""
        data = {"action": action,
                "method": method,
                "args": args,
                "print_it": print_it,
                "text_it": text_it,
                "say_it": say_it,
                }
        self.action_queue.put(data)

    def misunderstand(self, confidence, text_it=False, say_it=False):
        """bad understanding"""
        # TODO add text_it and say_it
        if confidence < 0.8 and confidence > 0.5:
            msg = gtt("I need a confirmation, Could you repeat please ?")
            self.logger.warning("NLU: misunderstood: {}".format(msg))
            # TODO ask a confirmation
        if confidence < 0.5:
            msg = gtt("Sorry, I just don't get it")
            self.logger.warning("NLU: misunderstood: {}".format(msg))
        if say_it is True:
            self._say(msg)
        if text_it is True:
            return msg
            # TODO say it

    def stop(self):
        """Stop NLU process"""
        self._must_run = False
        self.terminate()

    def run(self):
        """Text to understand"""
        self._must_run = True
        while self._must_run:
            try:
                say_it, text = self.nlu_queue.get(timeout=1)
            except Empty:
                # self.logger.debug("No text to understand received")
                continue
            self.logger.debug("Text received: {}".format(text))
            self.logger.debug("Say_it received: {}".format(say_it))
            loop = asyncio.get_event_loop()
            self._understanding = True
            # TODO: try/except
            speech_args = self._settings['speech']
            ret = loop.run_until_complete(
                understand_text(speech_args['url'],
                                speech_args['app_id'],
                                unhexlify(speech_args['app_key']),
                                # context_tag=credentials['context_tag'],
                                "master",
                                text,
                                speech_args['language'],
                                self.logger,
                                ))
            self._understanding = False
            self.logger.debug("Result: {}".format(ret))
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
                    action, method = intent.get("value").split("__")
                    # Run action
                    # TODO add parameters
                    self._run_action(action, method, {}, False, True, say_it)


class NLUError(Exception):
    """Base class for NLU exceptions"""
    pass
