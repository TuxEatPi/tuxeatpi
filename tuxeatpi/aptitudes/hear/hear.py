import os
from queue import Empty
import time
from datetime import timedelta, datetime
import threading

import pyaudio
from pocketsphinx.pocketsphinx import Decoder

from tuxeatpi.aptitudes.common import Aptitude, capability, can_transmit
from tuxeatpi.libs.lang import gtt, doc
from tuxeatpi.transmission import create_transmission

# SILENT DETECTION
# TODO adjust it
FS_NB_CHUNK = 100
NB_CHUNK = 5
THRESHOLD = 500


class Hear(Aptitude, threading.Thread):

    def __init__(self, tuxdroid):
        threading.Thread.__init__(self)
        Aptitude.__init__(self, tuxdroid)
        self.start_time = time.time()
        self._config = Decoder.default_config()
        # TODO raise an error
        if not self._prepare_decoder():
            self._must_run = False

    def _prepare_decoder(self):
        """Set decoder config"""
        # prepare config
        self._hotword = self.settings['speech']['hotword']
        # self._answer = self.settings['hotword']['answer']
        if not os.path.isdir("pocketsphinx-data"):
            raise HotWordError("Missing pocketsphinx-data folder. Please run `make hotword`")

        acoustic_model = os.path.join("pocketsphinx-data",
                                      self.settings['speech']['language'],
                                      'acoustic-model',
                                      )
        language_model = os.path.join("pocketsphinx-data",
                                      self.settings['speech']['language'],
                                      'language-model.lm.bin',
                                      )
        pocket_dict = os.path.join("pocketsphinx-data",
                                   self.settings['speech']['language'],
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

    def run(self):
        """Listen for NLU"""
        self._rerun = True
        self._must_run = True
        while self._rerun:
            self.logger.debug("starting listening hotword %s", self._hotword)
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

                if self._decoder.hyp() and self._decoder.hyp().hypstr == self._hotword:
                    self.logger.debug("Hotword detected")
                    # TODO answering
                    #self._answering()
                    # TODO create tranmission for audio nlu
                    self._rerun = True
                    break
            self._decoder.end_utt()

