"""Hotword component"""

import os
from multiprocessing import Process

import pyaudio
from pocketsphinx.pocketsphinx import Decoder


class HotWord(Process):
    """Define hotword component

    For now hotword uses pocketsphinx with speech_recognition
    """
    def __init__(self, settings, logger):
        Process.__init__(self)
        # Set logger
        self.logger = logger.getChild("Hotword")
        self.logger.debug("Initialization")
        # Init private attributes
        self._settings = settings
        self._must_run = True
        self._config = Decoder.default_config()
        if not self.prepare_decoder():
            self._must_run = False

    def prepare_decoder(self):
        """Set decoder config"""
        # prepare config
        self._hotword = self._settings['hotword']['hotword']
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

    def stop(self):
        """Stop process"""
        self._must_run = False
        self.terminate()

    def run(self):
        """Text to speech"""
        rerun = True
        self.logger.debug("starting listening hotword %s", self._hotword)
        while rerun:
            rerun = False
            self._paudio = pyaudio.PyAudio()
            stream = self._paudio.open(format=pyaudio.paInt16, channels=1, rate=16000,
                                       input=True, frames_per_buffer=1024)
            stream.start_stream()
            self._paudio.get_default_input_device_info()

            self._decoder.start_utt()
            while self._must_run:
                buf = stream.read(1024)
                self._decoder.process_raw(buf, False, False)
                if self._decoder.hyp() and self._decoder.hyp().hypstr == self._hotword:
                    self.logger.debug("Hotword detected")
                    # TODO run nlu audio detection
                    rerun = True
                    break
            self._decoder.end_utt()


class HotWordError(Exception):
    """Base class for voice exceptions"""
    pass
