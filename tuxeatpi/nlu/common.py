"""Utils for Nuance Mix Nlu services"""
import asyncio
import base64
import binascii
import datetime
import email.utils
import hashlib
import hmac
import itertools
import os
import sys
import urllib.parse

import aiohttp
import pyaudio
import speex


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


@asyncio.coroutine
def understand_audio(loop, url, app_id, app_key,  # pylint: disable=R0914
                     context_tag, language, recorder, logger):
    """Try to understant audio"""
    rate = recorder.rate
    resampler = None

    if rate >= 16000:
        if rate != 16000:
            resampler = speex.SpeexResampler(1, rate, 16000)  # pylint: disable=E1101
        audio_type = 'audio/x-speex;mode=wb'
    else:
        if rate != 8000:
            resampler = speex.SpeexResampler(1, rate, 8000)  # pylint: disable=E1101
        audio_type = 'audio/x-speex;mode=nb'

    client = WebsocketConnection(url, logger)
    yield from client.connect(app_id, app_key)

    client.send_message({
        'message': 'connect',
        'device_id': '55555500000000000000000000000000',
        'codec': audio_type
    })

    _, msg = yield from client.receive()
    logger.debug(msg)  # Should be a connected message

    client.send_message({
        'message': 'query_begin',
        'transaction_id': 123,

        'command': 'NDSP_ASR_APP_CMD',
        'language': language,
        'context_tag': context_tag,
    })

    client.send_message({
        'message': 'query_parameter',
        'transaction_id': 123,

        'parameter_name': 'AUDIO_INFO',
        'parameter_type': 'audio',

        'audio_id': 456
    })

    client.send_message({
        'message': 'query_end',
        'transaction_id': 123,
    })

    client.send_message({
        'message': 'audio',
        'audio_id': 456,
    })

    if audio_type == 'audio/x-speex;mode=wb':
        encoder = speex.WBEncoder()  # pylint: disable=E1101
    else:
        encoder = speex.NBEncoder()  # pylint: disable=E1101

    keyevent = asyncio.Event()

    def keyevent_callback():
        """Key event callback"""
        sys.stdin.readline()
        keyevent.set()

    loop.add_reader(sys.stdin, keyevent_callback)

    keytask = asyncio.ensure_future(keyevent.wait())
    audiotask = asyncio.ensure_future(recorder.dequeue())
    receivetask = asyncio.ensure_future(client.receive())

    audio = b''
    rawaudio = b''

    print('Recording, press any key to stop...')

    # f = open('debug.raw', 'wb')
    # fr = open('pre.raw', 'wb')
    while not keytask.done():
        while len(rawaudio) > 320*recorder.channels*2:
            count = len(rawaudio)
            if count > 320*4*recorder.channels*2:
                count = 320*4*recorder.channels*2

            procsamples = b''
            if recorder.channels > 1:
                for i in range(0, count, 2*recorder.channels):
                    procsamples += rawaudio[i:i+1]
            else:
                procsamples = rawaudio[:count]

            rawaudio = rawaudio[count:]

            if resampler:
                audio += resampler.process(procsamples)
            else:
                audio += procsamples

        while len(audio) > encoder.frame_size*2:
            # f.write(audio[:encoder.frame_size*2])
            coded = encoder.encode(audio[:encoder.frame_size*2])
            client.send_audio(coded)
            audio = audio[encoder.frame_size*2:]

        yield from asyncio.wait((keytask, audiotask, receivetask),
                                return_when=asyncio.FIRST_COMPLETED,
                                loop=loop)

        if audiotask.done():
            more_audio = audiotask.result()
            # fr.write(more_audio)
            rawaudio += more_audio
            audiotask = asyncio.ensure_future(recorder.dequeue())

        if receivetask.done():  # pylint: disable=E1101
            _, msg = receivetask.result()  # pylint: disable=E1101
            logger.debug(msg)

            if msg['message'] == 'query_end':
                client.close()
                return

            receivetask = asyncio.ensure_future(client.receive())

    # f.close()
    # fr.close()

    client.send_message({
        'message': 'audio_end',
        'audio_id': 456,
    })

    while True:
        yield from asyncio.wait((receivetask,), loop=loop)
        _, msg = receivetask.result()  # pylint: disable=E1101
        logger.debug(msg)

        if msg['message'] == 'query_end':
            break

        receivetask = asyncio.ensure_future(client.receive())

    client.close()


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


# ------------------------------
#
#
# def main():
#     """
#     For CLI usage:
#
#         python nlu.py --help
#
#     For audio + NLU:
#
#         python nlu.py audio
#         # 1. Start recording when prompted;
#         # 2. Press <enter> when done.
#
#     For text + NLU:
#
#         python nlu.py text 'This is the sentence you want to test'
#
#     """
#
#     parser = argparse.ArgumentParser(description='Mix.nlu sample application')
#
#     # Check for credentials file
#     parser.add_argument('--config', '-c',
#                         dest='config',
#                         default='creds.json',
#                         help='JSON configuration file',
#                         type=argparse.FileType('r'),
#                         )
#
#     # Add two subcommands: `audio` and `text`
#     subparsers = parser.add_subparsers(dest='command', title='commands')
#     subparsers.required = True
#
#     subparsers.add_parser('audio', help='Record audio from your microphone')
#
#     parser_text = subparsers.add_parser('text', help='Specify a text sentence from the CLI')
#     parser_text.add_argument('sentence', help='Sentence to understand (enclose in quotes)')
#
#     args = parser.parse_args()
#
#     # Read the configuration file
#     credentials = json.load(args.config, encoding='utf-8')
#
#     loop = asyncio.get_event_loop()
#
#     if args.command == 'text':
#         loop.run_until_complete(understand_text(
#             loop,
#             credentials['url'],
#             credentials['app_id'],
#             binascii.unhexlify(credentials['app_key']),
#             context_tag=credentials['context_tag'],
#             text_to_understand=args.sentence,
#             language=credentials['language']))
#
#     elif args.command == 'audio':
#
#         with Recorder(loop=loop) as recorder:
#
#             loop.run_until_complete(understand_audio(
#                 loop,
#                 credentials['url'],
#                 credentials['app_id'],
#                 binascii.unhexlify(credentials['app_key']),
#                 context_tag=credentials['context_tag'],
#                 language=credentials['language'],
#                 recorder=recorder))
