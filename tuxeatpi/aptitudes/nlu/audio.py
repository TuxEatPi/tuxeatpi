"""NLU audio module"""

import asyncio
from binascii import unhexlify
import logging

import audioop
import speex

from tuxeatpi.aptitudes.nlu.common import Recorder, WebsocketConnection


# SILENT DETECTION
# TODO adjust it
FS_NB_CHUNK = 100
NB_CHUNK = 5
THRESHOLD = 500


def nlu_audio(settings):
    """NLU audio wrapper"""
    logger = logging.getLogger(name="tep").getChild("aptitudes").getChild("nlu").getChild("audio")
    speech_args = settings['speech']
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        logger.debug("Get New event loop")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    interpretations = {}
    with Recorder(loop=loop) as recorder:
        interpretations = loop.run_until_complete(understand_audio(
            loop,
            speech_args['url'],
            speech_args['app_id'],
            unhexlify(speech_args['app_key']),
            # context_tag=credentials['context_tag'],
            "master",
            speech_args['language'],
            recorder=recorder,
            logger=logger))
    # loop.close()
    if interpretations is False:
        # The user did not speak
        return {}
    else:
        return interpretations


def _silent_detection(audio, silent_list, first_silent_done, logger):
    """Analyse audio chunk to determine if this is a silent

    return False: the user did NOT speak
    return None: the user is speaking or we are waiting for it
    return True: the user had finished to speack
    """
    # Get rms for this chunk
    audio_rms = audioop.rms(audio, 2)
    # Detect first silent
    if first_silent_done is False:
        logger.debug("Audio level: %s", audio_rms)
        if audio_rms < THRESHOLD:
            logger.debug("Waiting for user speaking")
            silent_list.append(True)
        else:
            logger.debug("User is maybe starting to speak")
            silent_list.append(False)
        if len([s for s in silent_list if s is False]) > 5:
            logger.debug("User is starting to speak")
            silent_list = []
            first_silent_done = True
        if len(silent_list) > FS_NB_CHUNK:
            logger.debug("The user did NOT speak")
            return False, silent_list, first_silent_done
    else:
        silent_list.append(True if audio_rms < THRESHOLD else False)
        if len(silent_list) > NB_CHUNK:
            logger.debug("The user is speaking. Level: %d", audio_rms)
            silent_list.pop(0)
        if len(silent_list) == NB_CHUNK and all(silent_list):
            logger.debug("The user has finished to speak")
            return True, silent_list, first_silent_done
    return None, silent_list, first_silent_done


@asyncio.coroutine
def understand_audio(loop, url, app_id, app_key, context_tag=None,  # pylint: disable=R0914
                     language='eng-USA', recorder=None, logger=None):
    """Trying to understand audio"""
    audio = b''
    rawaudio = b''

    # Prepare audio
    rate = recorder.rate
    resampler = None

    if rate >= 16000:
        if rate != 16000:
            resampler = speex.SpeexResampler(1, rate, 16000)  # pylint: disable=E1101
    else:
        if rate != 8000:
            resampler = speex.SpeexResampler(1, rate, 8000)  # pylint: disable=E1101

    audio_type = 'audio/x-speex;mode=wb'
    encoder = speex.WBEncoder()  # pylint: disable=E1101

    # Websocket client
    client = WebsocketConnection(url, logger)
    yield from client.connect(app_id, app_key)

    # Init Nuance communication
    client.send_message({
        'message': 'connect',
        'device_id': '55555500000000000000000000000000',
        'codec': audio_type
    })

    _, msg = yield from client.receive()
    # logger.debug(msg)  # Should be a connected message

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

    audiotask = asyncio.ensure_future(recorder.dequeue())
    receivetask = asyncio.ensure_future(client.receive())

    # Prepare silent vars
    silent_list = []
    first_silent_done = False
    while True:
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
            coded = encoder.encode(audio[:encoder.frame_size*2])
            client.send_audio(coded)
            audio = audio[encoder.frame_size*2:]

        yield from asyncio.wait((audiotask, receivetask),
                                return_when=asyncio.FIRST_COMPLETED,
                                loop=loop)

        # SILENT DETECTION
        ret, silent_list, first_silent_done = _silent_detection(audio, silent_list,
                                                                first_silent_done, logger)
        if ret is False:
            return ret
        if ret is True:
            break

        if audiotask.done():
            more_audio = audiotask.result()
            rawaudio += more_audio
            audiotask = asyncio.ensure_future(recorder.dequeue())

        if receivetask.done():
            _, msg = receivetask.result()
            logger.debug(msg)

            if msg['message'] == 'query_end':
                client.close()
                return

            receivetask = asyncio.ensure_future(client.receive())

    recorder.stop()

    logger.debug("Send last message to Mix")
    client.send_message({
        'message': 'audio_end',
        'audio_id': 456,
    })

    interpretation = {}
    while True:
        yield from asyncio.wait((receivetask,), loop=loop)
        _, msg = receivetask.result()
        logger.debug(msg)

        if msg['message'] == 'query_end':
            break
        else:
            interpretation = msg

        receivetask = asyncio.ensure_future(client.receive())

    client.close()
    return interpretation
