"""Voice component"""

import asyncio
from binascii import unhexlify
from queue import Empty

from tuxeatpi.nlu.common import WebsocketConnection, NLUBase


class NLUText(NLUBase):
    """Define NLU component

    For now NLU use Nuance communications services
    """
    def __init__(self, settings, action_queue, nlu_queue, tts_queue, logger):
        NLUBase.__init__(self, settings, action_queue, nlu_queue, tts_queue, logger)

    def run(self):
        """Text to understand"""
        while self._must_run:
            try:
                say_it, text = self.nlu_queue.get(timeout=1)
            except Empty:
                self.logger.debug("No text to understand received")
                continue
            # Reload config from file because we are in an other Process
            self._settings.reload()
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
                    self._misunderstand(0, True, say_it)
                elif intent.get("confidence") < 0.8:
                    # I'm not sure to undestand :/
                    self._misunderstand(intent.get("confidence"), True, say_it)
                else:
                    # Check intent name
                    if len(intent.get("value").split("__")) != 2:
                        self.logger.critical("BAD Intent name: {}".format(intent.get("value")))
                        self._misunderstand(0, True, say_it)
                    # Run function with parameters
                    action, method = intent.get("value").split("__")
                    # Run action
                    # TODO add parameters from NLU response
                    self._run_action(action, method, {}, False, True, say_it)


class NLUError(Exception):
    """Base class for NLU exceptions"""
    pass


@asyncio.coroutine
def understand_text(url, app_id, app_key, context_tag, text_to_understand, language, logger):
    """Try to understand text"""
    client = WebsocketConnection(url, logger)
    yield from client.connect(app_id, app_key)

    client.send_message({'message': 'connect',
                         'device_id': '55555500000000000000000000000000',
                         # 'codec': audio_type
                         })

    _, msg = yield from client.receive()
    logger.debug(msg)  # Should be a connected message

    client.send_message({
        'message': 'query_begin',
        'transaction_id': 123,

        'command': 'NDSP_APP_CMD',
        'language': language,
        'context_tag': context_tag,
    })

    client.send_message({
        'message': 'query_parameter',
        'transaction_id': 123,

        'parameter_name': 'REQUEST_INFO',
        'parameter_type': 'dictionary',

        'dictionary': {
            'application_data': {
                'text_input': text_to_understand,
            }
        }
    })

    client.send_message({
        'message': 'query_end',
        'transaction_id': 123,
    })

    ret = ""
    while True:
        _, msg = yield from client.receive()

        if msg['message'] == 'query_end':
            break
        ret = msg

    client.close()
    return ret
