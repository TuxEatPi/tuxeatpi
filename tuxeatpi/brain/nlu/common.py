"""Utils for Nuance Mix Nlu services"""
import asyncio
import base64
import binascii
import datetime
from multiprocessing import Process, Queue, Manager
import logging
import email.utils
import hashlib
import hmac
import itertools
import os
import urllib.parse

import aiohttp
import pyaudio

from tuxeatpi.libs.lang import gtt
from tuxeatpi.libs.websocket import AbstractWebsocketConnection


class WebsocketConnection(AbstractWebsocketConnection):
    """Websocket client"""

    def __init__(self, url, logger):
        AbstractWebsocketConnection.__init__(self, url, logger)

    @asyncio.coroutine
    def connect(self, app_id, app_key, use_plaintext=True):
        """Connect to the websocket"""
        date = datetime.datetime.utcnow()
        sec_key = base64.b64encode(os.urandom(16))

        if use_plaintext:
            params = {
                'app_id': app_id,
                'algorithm': 'key',
                'app_key': binascii.hexlify(app_key),
            }
        else:
            datestr = date.replace(microsecond=0).isoformat()
            params = {
                'date': datestr,
                'app_id': app_id,
                'algorithm': 'HMAC-SHA-256',
                'signature': self.sign_credentials(datestr, app_key, app_id),
            }

        response = yield from aiohttp.request(
            'get', self.url + '?' + urllib.parse.urlencode(params),
            headers={
                'UPGRADE': 'WebSocket',
                'CONNECTION': 'Upgrade',
                'SEC-WEBSOCKET-VERSION': '13',
                'SEC-WEBSOCKET-KEY': sec_key.decode(),
            })

        if response.status == 401 and not use_plaintext:
            if 'Date' in response.headers:
                server_date = email.utils.parsedate_to_datetime(response.headers['Date'])
                if server_date.tzinfo is not None:
                    server_date = (server_date - server_date.utcoffset()).replace(tzinfo=None)
            else:
                server_date = yield from response.read()
                server_date = datetime.datetime.strptime(server_date[:19].decode('ascii'),
                                                         "%Y-%m-%dT%H:%M:%S")

            # Use delta on future requests
            date_delta = server_date - date

            print("Retrying authorization (delta=%s)" % date_delta)

            datestr = (date + date_delta).replace(microsecond=0).isoformat()
            params = {
                'date': datestr,
                'algorithm': 'HMAC-SHA-256',
                'app_id': app_id,
                'signature': self.sign_credentials(datestr, app_key, app_id),
            }

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

    @staticmethod
    def sign_credentials(datestr, app_key, app_id):
        """Handle credentials"""
        value = datestr.encode('ascii') + b' ' + app_id.encode('utf-8')
        return hmac.new(app_key, value, hashlib.sha256).hexdigest()


class Recorder:
    """Record voice from mic"""

    def __init__(self, device_index=None, rate=None, channels=None, loop=None):

        # Audio configuration
        self.audio = pyaudio.PyAudio()

        if device_index is None:
            self.pick_default_device_index()
        else:
            self.device_index = device_index

        if rate is None or channels is None:
            self.pick_default_parameters()
        else:
            self.rate = rate
            self.channels = channels

        self.recstream = None

        # Event loop
        if loop:
            self.loop = loop
        else:
            self.loop = asyncio.get_event_loop()
        self.queue_event = asyncio.Event(loop=self.loop)
        self.audio_queue = []

    def __enter__(self):
        self.recstream = self.audio.open(
            self.rate,
            self.channels,
            pyaudio.paInt16,
            input=True,
            input_device_index=self.device_index,
            stream_callback=self.callback)
        return self

    def __exit__(self, error_type, value, traceback):
        if self.recstream is not None:
            self.recstream.close()

    def enqueue(self, audio):  # pylint: disable=C0111
        self.audio_queue.append(audio)
        self.queue_event.set()

    @asyncio.coroutine
    def dequeue(self):  # pylint: disable=C0111
        while True:
            self.queue_event.clear()
            if len(self.audio_queue):
                return self.audio_queue.pop(0)
            yield from self.queue_event.wait()

    def callback(self, in_data, frame_count, time_info, status_flags):  # pylint: disable=W0613
        """Callback function"""
        self.loop.call_soon_threadsafe(self.enqueue, in_data)
        return (None, pyaudio.paContinue)

    def pick_default_device_index(self):  # pylint: disable=C0111
        try:
            device_info = self.audio.get_default_input_device_info()
            self.device_index = device_info['index']
        except IOError:
            raise RuntimeError("No Recording Devices Found")

    def pick_default_parameters(self):  # pylint: disable=C0111
        rates = [
            16000,
            32000,
            48000,
            96000,
            192000,
            22050,
            44100,
            88100,
            8000,
            11025,
        ]
        channels = [1, 2]

        # Add device spefic information
        info = self.audio.get_device_info_by_index(self.device_index)
        rates.append(info['defaultSampleRate'])
        channels.append(info['maxInputChannels'])

        for (rate, channel) in itertools.product(rates, channels):
            if self.audio.is_format_supported(rate,
                                              input_device=self.device_index,
                                              input_channels=channel,
                                              input_format=pyaudio.paInt16):
                (self.rate, self.channels) = (rate, channel)
                break
        else:
            # If no (rate, channel) combination is found, raise an error
            error = "Couldn't find recording parameters for device {}".format(self.device_index)
            raise RuntimeError(error)


class NLUBase(Process):
    """Define NLU base component
    """
    def __init__(self, settings):
        Process.__init__(self)
        # Set logger
        self.logger = logging.getLogger(name="tep").getChild("brain").getChild(self.__class__.__name__)
        self.logger.debug("Initialization")
        # Set queues
        self.queue_task = Queue()
        manager = Manager()
        self.task_done_dict = manager.dict()
#        self.tts_queue = tts_queue
#        self.action_queue = action_queue
        # Init private attributes
        self._settings = settings
        self._must_run = True

    def run(self):
        raise NotImplementedError

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

    def _misunderstand(self, confidence, text_it=False, say_it=False):
        """Bad understanding"""
        # TODO add text_it and say_it
        msg = ''
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
        try:
            self.terminate()
        except AttributeError:
            pass


def _misunderstand(confidence, logger):
    """Bad understanding"""
    # TODO add text_it and say_it
    msg = ''
    if confidence < 0.8 and confidence > 0.5:
        msg = gtt("I need a confirmation, Could you repeat please ?")
        logger.warning("NLU: misunderstood: {}".format(msg))
        # TODO ask a confirmation
    if confidence < 0.5:
        msg = gtt("Sorry, I just don't get it")
        logger.warning("NLU: misunderstood: {}".format(msg))
    if say_it is True:
        self._say(msg)
    if text_it is True:
        return msg
        # TODO say it


class NLUError(Exception):
    """Base class for NLU exceptions"""
    pass
