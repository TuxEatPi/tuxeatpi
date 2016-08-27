"""Module defining abstractWebsocket class"""

import asyncio
import json
import base64
import hashlib

from aiohttp import websocket


# This is a fixed string (constant), used in the Websockets protocol handshake
# in order to establish a conversation
WS_KEY = b"258EAFA5-E914-47DA-95CA-C5AB0DC85B11"


class AbstractWebsocketConnection(object):  # pylint: disable=R0801
    """WebSocket connection object to handle Nuance server communications"""
    MSG_JSON = 1
    MSG_AUDIO = 2

    def __init__(self, url, logger):
        self.url = url
        self.logger = logger
        self.connection = None
        self.response = None
        self.stream = None
        self.writer = None

    @asyncio.coroutine
    def connect(self, app_id, app_key, use_plaintext=True):
        """Connect to the websocket"""
        raise NotImplementedError

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
        self.logger.debug(msg)
        self.writer.send(json.dumps(msg))

    def send_audio(self, audio):
        """Send audio to the server"""
        self.writer.send(audio, binary=True)

    def close(self):
        """Close WebSocket connection"""
        self.writer.close()
        self.response.close()
        self.connection.close()

    @staticmethod
    def _handle_response_101(response):
        """handle response"""
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

    def _handshake(self, response, sec_key):
        """Websocket handshake"""
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
