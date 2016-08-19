"""Utils functions for Nuance Communications TTS services"""
# Get from https://github.com/Fadyazmy/harrawr/blob/master/wsclient.py

import base64
import binascii
import hashlib
import json
import os
import urllib.parse

import asyncio

import aiohttp
from aiohttp import websocket

try:
    import speex
except ImportError:
    speex = None

try:
    import opuslib.api as opus
except ImportError:
    opus = None

AUDIO_TYPES = [
    'audio/x-speex;mode=wb',
    'audio/opus;rate=16000',
    'audio/L16;rate=16000',
    'audio/16KADPCM;rate=16000'
]

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

VOICES = {"eng-USA": ["allison",
                      "ava",
                      "samantha",
                      "susan",
                      "zoe",
                      "tom",
                      ],
          "fra-CAN": ["audrey-ml",
                      "thomas",
                      "aurelie"
                      ]
          }

# This is a fixed string (constant), used in the Websockets protocol handshake
# in order to establish a conversation
WS_KEY = b"258EAFA5-E914-47DA-95CA-C5AB0DC85B11"


class WebsocketConnection:
    """WebSocket connection object to handle Nuance server communications"""
    MSG_JSON = 1
    MSG_AUDIO = 2

    @asyncio.coroutine
    def connect(self, url, app_id, app_key):
        """Connect to the server"""
        sec_key = base64.b64encode(os.urandom(16))

        params = {'app_id': app_id, 'algorithm': 'key', 'app_key': binascii.hexlify(app_key)}

        response = yield from aiohttp.request(
            'get', url + '?' + urllib.parse.urlencode(params),
            headers={
                'UPGRADE': 'WebSocket',
                'CONNECTION': 'Upgrade',
                'SEC-WEBSOCKET-VERSION': '13',
                'SEC-WEBSOCKET-KEY': sec_key.decode(),
            })

        if response.status != 101:
            info = "%s %s\n" % (response.status, response.reason)
            for (key, val) in response.headers.items():
                info += '%s: %s\n' % (key, val)
            info += '\n%s' % (yield from response.read()).decode('utf-8')

            if response.status == 401:
                raise RuntimeError("Authorization failure:\n%s" % info)
            elif response.status >= 500 and response.status < 600:
                raise RuntimeError("Server error:\n%s" % info)
            elif response.headers.get('upgrade', '').lower() != 'websocket':
                raise ValueError("Handshake error - Invalid upgrade header")
            elif response.headers.get('connection', '').lower() != 'upgrade':
                raise ValueError("Handshake error - Invalid connection header")
            else:
                raise ValueError("Handshake error: Invalid response status:\n%s" % info)

        # Using WS_KEY in handshake
        key = response.headers.get('sec-websocket-accept', '').encode()
        match = base64.b64encode(hashlib.sha1(sec_key + WS_KEY).digest())
        if key != match:
            raise ValueError("Handshake error - Invalid challenge response")

        # switch to websocket protocol
        self.connection = response.connection
        self.stream = self.connection.reader.set_parser(websocket.WebSocketParser)
        self.writer = websocket.WebSocketWriter(self.connection.writer)
        self.response = response

    @asyncio.coroutine
    def receive(self):
        """Handle server response"""
        wsmsg = yield from self.stream.read()
        if wsmsg.tp == 1:
            return (self.MSG_JSON, json.loads(wsmsg.data))
        else:
            return (self.MSG_AUDIO, wsmsg.data)

    def send_message(self, msg):
        """Send json message to the server"""
        self.writer.send(json.dumps(msg))

    def send_audio(self, audio):
        """Send audio to the server"""
        self.writer.send(audio, binary=True)

    def close(self):
        """Close WebSocket connection"""
        self.writer.close()
        self.response.close()
        self.connection.close()


def do_synthesis(url, app_id, app_key, language, voice, input_text,
                 audio_player, logger, use_speex=False, use_opus=False):
    """The TTS function using Nuance Communications services"""

    if use_speex is True and speex is None:
        print('ERROR: Speex encoding specified but python-speex module unavailable')
        return
    elif use_opus is True and opus is None:
        print('ERROR: Opus encoding specified but python-opuslib module unavailable')
        return

    if use_speex:
        audio_type = 'audio/x-speex;mode=wb'
    elif use_opus:
        audio_type = 'audio/opus;rate=16000'
    else:
        audio_type = 'audio/L16;rate=16000'

    client = WebsocketConnection()
    yield from client.connect(url, app_id, app_key)

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


def _get_opus_decoder_func(decoder):
    """Create function for Opus codec"""
    def decoder_func(msg):
        """Opus decoder function"""
        opus.decoder.decode(decoder, msg, len(msg), 1920, False, 1)

    return decoder_func
