"""Aptitude for wake up TuxDroid using voice (wake up word)"""

import os
import wave

import pyaudio
from pocketsphinx.pocketsphinx import Decoder

from tuxeatpi.aptitudes.common import ThreadedAptitude, capability, can_transmit
from tuxeatpi.libs.lang import gtt


# SILENT DETECTION
# TODO adjust it
FS_NB_CHUNK = 100
NB_CHUNK = 5
THRESHOLD = 500


class Hear(ThreadedAptitude):
    """Wake up word aptitude"""

    def __init__(self, tuxdroid):
        ThreadedAptitude.__init__(self, tuxdroid)

        self._answer_sound_path = "sounds/answer.wav"
        self._config = Decoder.default_config()

    def help_(self):
        # TODO do it
        pass

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
        return True

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
        # Close file
        f_ans.close()
        # Close stream
        stream.stop_stream()
        stream.close()

    def stop(self):
        """Stop process"""
        self._rerun = False
        ThreadedAptitude.stop(self)

    def run(self):
        """Listen for NLU"""
        self._rerun = True
        self._must_run = True
        while self._rerun:
            # TODO raise an error
            self.logger.info("Starting hear aptitudes")
            if self._prepare_decoder() is False:
                self._rerun = False
                self._must_run = False
                self.logger.critical("Error starting hear aptitudes")
                return
            else:
                self._must_run = True

            self.logger.debug("starting listening hotword `%s` with lang %s",
                              self._hotword,
                              self.settings['speech']['language'])
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
                    self.wake_up_work()
                    self._rerun = True
                    break
            self._decoder.end_utt()

    @capability(gtt("Give your my attention and listen to you"))
    # @can_transmit
    def wake_up_work(self):
        """Wake up work capability

        Answer to the speaker and create a transmission for audio nlu
        """
        # answering
        self._answering()
        # create tranmission for audio nlu
        content = {"arguments": {}}
        tmn = self.create_transmission("hear", "aptitudes.nlu.audio", content)
        self.wait_for_answer(tmn.id_)

    def reload_decoder(self):
        """Reload decoder

        This is usefull when lang changes
        """
        self.logger.info("Reload hear aptitude")
        self._must_run = False
        self._rerun = True


class HotWordError(Exception):
    """Base class for hotword exceptions"""
    pass
