"""Voice component"""

import asyncio
from binascii import unhexlify
from queue import Empty
import logging

import aiohttp

from tuxeatpi.brain.nlu.common import WebsocketConnection, NLUBase


class NLUText(NLUBase):

#    def __init__(self, settings, action_queue, nlu_queue):
#        NLUBase.__init__(self, settings, action_queue, nlu_queue, tts_queue)

    def run(self):
        """Text to understand"""
        while self._must_run:
            try:
                id_, text = self.queue_task.get(timeout=1)
            except Empty:
#                self.logger.debug("No text to understand received")
                continue
            result = {"module": None,
                      "method": None,
                      "arguments": None,
                      "confidence": None,
                      "need_confirmation": False,
                      "error": None,
                      }
            # Reload config from file because we are in an other Process
            self._settings.reload()
            self.logger.debug("Text received: {}".format(text))
            loop = asyncio.get_event_loop()
            # TODO: try/except
            speech_args = self._settings['speech']
            ret = loop.run_until_complete(
                _nlu_text(speech_args['url'],
                          speech_args['app_id'],
                          unhexlify(speech_args['app_key']),
                          # context_tag=credentials['context_tag'],
                          "master",
                          text,
                          speech_args['language'],
                          self.logger,
                          ))
            if isinstance(ret, Exception):
                self.logger.critical("Can not understant text '%s'", text)
                self.logger.critical("Error: %s", ret)
                result['error'] = str(ret)
                self.task_done_dict[id_] = result
                continue

            self.logger.debug("Result: %s", ret)
            interpretations = ret.get("nlu_interpretation_results", {}).\
                get("payload", {}).get("interpretations", {})
            # TODO: what about if len(interpretations) > 1 ??
            self.logger.info("Nb interpretations: %s", len(interpretations))
            for interpretation in interpretations:
                intent = interpretation.get("action", {}).get("intent", {})
                self.logger.info("Intent: %s", intent.get("value"))
                result['confidence'] = intent.get("confidence")
                self.logger.info("Confidence: %s", result["confidence"])
                # Get concepts
                arguments = {}
                for name, data in interpretation.get("concepts", {}).items():
                    arguments[name] = data[0].get('value')
                self.logger.info("Arguments: %s", arguments)
                # TODO log arguments
                if intent.get("value") == "NO_MATCH":
                    # I don't understand :/
                    self.task_done_dict[id_] = result
                    continue

                # Check intent
                if len(intent.get("value").split("__")) != 2:
                    self.logger.critical("BAD Intent name: {}".format(intent.get("value")))
                    self.task_done_dict[id_] = result
                    continue

                module, method = intent.get("value").split("__")
                result['module'] = module
                result['method'] = method
                result['arguments'] = arguments
                if intent.get("confidence") < 0.5:
                    # I'm not sure to understand :/
                    self.logger.info("Module: %s", module)
                    self.logger.info("Method: %s", method)
                    self.logger.info("Need confirmation - confidence: %s", confidence)
                    result['need_confirmation'] = True

                # Return result
                self.task_done_dict[id_] = result


@asyncio.coroutine
def _nlu_text(url, app_id, app_key, context_tag, text_to_understand, language, logger):
    """Try to understand text"""
    client = WebsocketConnection(url, logger)
    try:
        yield from client.connect(app_id, app_key)
    except aiohttp.errors.ClientOSError as exp:
        return exp

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
