"""NLU audio module"""

import asyncio
from binascii import unhexlify
import os
import wave

import audioop
import speex
import pyaudio
from pocketsphinx.pocketsphinx import Decoder

from tuxeatpi.nlu.common import Recorder, WebsocketConnection, NLUBase


# SILENT DETECTION
# TODO adjust it
FS_NB_CHUNK = 100
NB_CHUNK = 5
THRESHOLD = 500


class NLUAudio(NLUBase):
    """Define NLUAudio component

    For now hotword uses pocketsphinx with speech_recognition
    and Nuance services has NLU
    """
    def __init__(self, settings, action_queue, tts_queue, logger):
        NLUBase.__init__(self, settings, action_queue, None, tts_queue, logger)
        # Init private attributes
        self._rerun = True

        self._answer_sound_path = "sounds/answer.wav"
        self._config = Decoder.default_config()
        if not self._prepare_decoder():
            self._must_run = False

    def _prepare_decoder(self):
        """Set decoder config"""
        # prepare config
        self._hotword = self._settings['speech']['hotword']
        # self._answer = self._settings['hotword']['answer']
        if not os.path.isdir("pocketsphinx-data"):
            raise HotWordError("Missing pocketsphinx-data folder. Please run `make hotword`")

        acoustic_model = os.path.join("pocketsphinx-data",
                                      self._settings['speech']['language'],
                                      'acoustic-model',
                                      )
        language_model = os.path.join("pocketsphinx-data",
                                      self._settings['speech']['language'],
                                      'language-model.lm.bin',
                                      )
        pocket_dict = os.path.join("pocketsphinx-data",
                                   self._settings['speech']['language'],
                                   'pronounciation-dictionary.dict',
                                   )
        self._config.set_string('-logfn', "/dev/null")
        self._config.set_string('-hmm', acoustic_model)
        self._config.set_string('-lm', language_model)
        self._config.set_string('-dict', pocket_dict)
        try:
            self._decoder = Decoder(self._config)
        except RuntimeError:
            self.logger.critical("Error get audio decoder. Hotword not started")
            return False
        self._decoder.set_keyphrase('wakeup', self._hotword)
        self._decoder.set_search('wakeup')

    def stop(self):
        """Stop process"""
        self._rerun = False
        NLUBase.stop(self)

    def _answering(self):
        """Play the hotwoard confirmation sound"""
        f_ans = wave.open(self._answer_sound_path, "rb")
        stream = self._paudio.open(format=self._paudio.get_format_from_width(f_ans.getsampwidth()),
                                   channels=f_ans.getnchannels(),
                                   rate=f_ans.getframerate(),
                                   output=True)
        data = f_ans.readframes(1024)
        while len(data) > 0:
            stream.write(data)
            data = f_ans.readframes(1024)
        f_ans.close()

    def run(self):
        """Listen for NLU"""
        self._rerun = True
        self._must_run = True
        self.logger.debug("starting listening hotword %s", self._hotword)
        while self._rerun:
            self._rerun = False
            try:
                self._paudio = pyaudio.PyAudio()
                stream = self._paudio.open(format=pyaudio.paInt16, channels=1, rate=16000,
                                           input=True, frames_per_buffer=1024)
            except OSError:
                self.logger.warning("No audio device found can not listen for NLU")
                self.logger.warning("Disabling NLU audio")
                self._must_run = False
                self._rerun = False
                return
            stream.start_stream()
            self._paudio.get_default_input_device_info()

            self._decoder.start_utt()
            while self._must_run:
                buf = stream.read(1024)
                self._decoder.process_raw(buf, False, False)
                if not self.tts_queue.empty():
                    # If tts_queue is not empty, this means the Droid
                    # is currently speaking. So we don't want to it listen itself
                    # TODO replace this stuff by speaker annulation
                    continue
                if self._decoder.hyp() and self._decoder.hyp().hypstr == self._hotword:
                    self.logger.debug("Hotword detected")
                    # self.tts_queue.put(gtt(self._answer))
                    # self.tts_queue.put(gtt("mmm"))
                    self._answering()
                    ret = nlu_audio(self._settings, self.logger)

                    # GOT ACTIONS
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
                            self._misunderstand(0, True, True)
                        elif intent.get("confidence") < 0.8:
                            # I'm not sure to undestand :/
                            self._misunderstand(intent.get("confidence"), True, True)
                        else:
                            # Check intent name
                            if len(intent.get("value").split("__")) != 2:
                                self.logger.critical("BAD Intent name: "
                                                     "{}".format(intent.get("value")))
                                self._misunderstand(0, True, True)
                            # Run function with parameters
                            action, method = intent.get("value").split("__")
                            # Run action
                            # TODO add parameters from NLU response
                            self._run_action(action, method, {}, False, True, True)
                    # TODO run nlu audio detection
                    self._rerun = True
                    break
            self._decoder.end_utt()


def nlu_audio(settings, logger):
    """Wrapper for NLU audio"""
    speech_args = settings['speech']
    loop = asyncio.get_event_loop()
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
            return False
    else:
        silent_list.append(True if audio_rms < THRESHOLD else False)
        if len(silent_list) > NB_CHUNK:
            logger.debug("The user is speaking. Level: %d", audio_rms)
            silent_list.pop(0)
        if len(silent_list) == NB_CHUNK and all(silent_list):
            logger.debug("The user has finished to speak")
            return True
    return None


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
        ret = _silent_detection(audio, silent_list, first_silent_done, logger)
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


class HotWordError(Exception):
    """Base class for voice exceptions"""
    pass
