"""Hotword component"""

import os
from multiprocessing import Process
import wave

import pyaudio
from pocketsphinx.pocketsphinx import Decoder

from tuxeatpi.libs.lang import gtt
from tuxeatpi.nlu.audio import nlu_audio


class HotWord(Process):
    """Define hotword component

    For now hotword uses pocketsphinx with speech_recognition
    """
    def __init__(self, settings, action_queue, tts_queue, logger):
        Process.__init__(self)
        # Set logger
        self.logger = logger.getChild("Hotword")
        self.logger.debug("Initialization")
        self.tts_queue = tts_queue
        self.action_queue = action_queue
        # Init private attributes
        self._settings = settings
        self._must_run = True
        self._rerun = True
        self._answer_sound_path = "sounds/answer.wav"
        self._config = Decoder.default_config()
        if not self.prepare_decoder():
            self._must_run = False

    def prepare_decoder(self):
        """Set decoder config"""
        # prepare config
        self._hotword = self._settings['hotword']['hotword']
        self._answer = self._settings['hotword']['answer']
        acoustic_model = os.path.join(self._settings['hotword']['model_dir'],
                                      self._settings['speech']['language'],
                                      'acoustic-model',
                                      )
        language_model = os.path.join(self._settings['hotword']['model_dir'],
                                      self._settings['speech']['language'],
                                      'language-model.lm.bin',
                                      )
        pocket_dict = os.path.join(self._settings['hotword']['model_dir'],
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
        """Stop process"""
        self._must_run = False
        self._rerun = False
        self.terminate()

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
        """Text to speech"""
        self._rerun = True
        self._must_run = True
        self.logger.debug("starting listening hotword %s", self._hotword)
        while self._rerun:
            self._rerun = False
            self._paudio = pyaudio.PyAudio()
            stream = self._paudio.open(format=pyaudio.paInt16, channels=1, rate=16000,
                                       input=True, frames_per_buffer=1024)
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
                            self.misunderstand(0, True, True)
                        elif intent.get("confidence") < 0.8:
                            # I'm not sure to undestand :/
                            self.misunderstand(intent.get("confidence"), True, True)
                        else:
                            # Check intent name
                            if len(intent.get("value").split("__")) != 2:
                                self.logger.critical("BAD Intent name: "
                                                     "{}".format(intent.get("value")))
                                self.misunderstand(0, True, True)
                            # Run function with parameters
                            action, method = intent.get("value").split("__")
                            # Run action
                            # TODO add parameters from NLU response
                            self._run_action(action, method, {}, False, True, True)
                    # TODO run nlu audio detection
                    self._rerun = True
                    break
            self._decoder.end_utt()


class HotWordError(Exception):
    """Base class for voice exceptions"""
    pass
