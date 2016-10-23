"""Utils functions for Nuance Communications TTS services"""
# Get from https://github.com/Fadyazmy/harrawr/blob/master/wsclient.py

import asyncio
import base64
import binascii
import os
import urllib.parse

import pyaudio
import aiohttp

try:
    import speex
except ImportError:
    speex = None

try:
    import opuslib.api as opus
except ImportError:
    opus = None

from tuxeatpi.libs.websocket import AbstractWebsocketConnection

AUDIO_TYPES = [
    'audio/x-speex;mode=wb',
    'audio/opus;rate=16000',
    'audio/L16;rate=16000',
    'audio/16KADPCM;rate=16000'
]

CODECS = ('wav', 'speex', 'opus')

COMMANDS = [
    'NVC_ASR_CMD',
    'NVC_DATA_UPLOAD_CMD',
    'NVC_RESET_USER_PROFILE_CMD',
    'NVC_TTS_CMD',
    'NDMP_TTS_CMD',
    'DRAGON_NLU_ASR_CMD',
    'DRAGON_NLU_APPSERVER_CMD',
    'DRAGON_NLU_DATA_UPLOAD_CMD',
    'DRAGON_NLU_RESET_USER_PROFILE_CMD',
    'NDSP_ASR_APP_CMD'
    'NDSP_APP_CMD',
    'NDSP_UPLOAD_DATA_CMD',
    'NDSP_DELETE_ALL_DATA_CMD',
]

VOICES = {"eng-USA": {"female": "ava",
                      "male": "tom"},
          "fra-FRA": {"female": "aurelie",
                      "male": "thomas"},
          }


class WebsocketConnection(AbstractWebsocketConnection):
    """WebSocket connection object to handle Nuance server communications"""

    def __init__(self, url, logger):
        AbstractWebsocketConnection.__init__(self, url, logger)

    @asyncio.coroutine
    def connect(self, app_id, app_key, use_plaintext=True):
        """Connect to the server"""
        sec_key = base64.b64encode(os.urandom(16))

        params = {'app_id': app_id, 'algorithm': 'key', 'app_key': binascii.hexlify(app_key)}

        response = yield from aiohttp.request('get',
                                              self.url + '?' + urllib.parse.urlencode(params),
                                              headers={'UPGRADE': 'WebSocket',
                                                       'CONNECTION': 'Upgrade',
                                                       'SEC-WEBSOCKET-VERSION': '13',
                                                       'SEC-WEBSOCKET-KEY': sec_key.decode(),
                                                       })

        if response.status != 101:
            self._handle_response_101(response)

        self._handshake(response, sec_key)


def do_synthesis(url, app_id, app_key, language, voice, codec,
                 input_text, logger):
    """The TTS function using Nuance Communications services"""

    audio_player = pyaudio.PyAudio()

    if codec == "speex" and speex is None:
        print('ERROR: Speex encoding specified but python-speex module unavailable')
        return
    elif codec == "opus" and opus is None:
        print('ERROR: Opus encoding specified but python-opuslib module unavailable')
        return

    if codec == "speex":
        audio_type = 'audio/x-speex;mode=wb'
    elif codec == "opus":
        audio_type = 'audio/opus;rate=16000'
    else:
        audio_type = 'audio/L16;rate=16000'

    client = WebsocketConnection(url, logger)
    yield from client.connect(app_id, app_key)

    client.send_message({
        'message': 'connect',
        'codec': audio_type,
        'device_id': 'f0350aa9d98047a4b63d72ca5bfdf509',
        'user_id': '35228eb1afb54a3f8ba83754445a197c'
    })

    _, msg = yield from client.receive()
    # Should be a connected message
    logger.debug(msg)

    # synthesize
    client.send_message({
        'message': 'query_begin',
        'transaction_id': 123,
        'command': 'NVC_TTS_CMD',
        'language': language,
        'tts_voice': voice,
    })

    client.send_message({
        'message': 'query_parameter',
        'transaction_id': 123,

        'parameter_name': 'TEXT_TO_READ',
        'parameter_type': 'dictionary',
        'dictionary': {
            'audio_id': 789,
            'tts_input': input_text,
            'tts_type': 'text'
        }
    })

    client.send_message({
        'message': 'query_end',
        'transaction_id': 123,
    })

    # Create stream player
    stream = audio_player.open(format=audio_player.get_format_from_width(2),
                               # format=p.get_format_from_width(wf.getsampwidth()),
                               channels=1,
                               # channels=wf.getnchannels(),
                               rate=16000,
                               # rate=wf.getframerate(),
                               output=True)

    # Prepare decoder
    if audio_type == 'audio/L16;rate=16000':
        decoder_func = None
    elif audio_type == 'audio/x-speex;mode=wb':
        decoder = speex.WBDecoder()  # pylint: disable=E1101  ; I don't know why...
        decoder_func = decoder.decode
    elif audio_type == 'audio/opus;rate=16000':
        decoder = opus.decoder.create(16000, 1)
        decoder_func = _get_opus_decoder_func(decoder)

    else:
        # TODO raise Error
        print('ERROR: Need to implement encoding for %s!' % audio_type)
        return

    # Read and play sound
    while True:
        msg_type, msg = yield from client.receive()
        if msg_type == client.MSG_JSON:
            logger.debug(msg)
            if msg['message'] == 'query_end':
                break
        else:
            if decoder_func is not None:
                msg = decoder_func(msg)
            logger.info("Start sentence")
            stream.write(msg)
            logger.info("End sentence")

    # Close stream and client
    client.close()
    stream.stop_stream()
    stream.close()
    audio_player.terminate()


def _get_opus_decoder_func(decoder):
    """Create function for Opus codec"""
    def decoder_func(msg):
        """Opus decoder function"""
        opus.decoder.decode(decoder, msg, len(msg), 1920, False, 1)

    return decoder_func
