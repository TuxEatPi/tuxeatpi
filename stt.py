"""
Basic Speech-To-Text tools are stored here
"""

import pyaudio
import speech_recognition

from sphinxbase.sphinxbase import Config, Config_swigregister
from pocketsphinx.pocketsphinx import Decoder


from os.path import join
from os import path
import speech_recognition as sr
#####################
#    DIRECTORIES    #
#####################
#MODEL_DIR = path.join(SR_DIR, 'pocketsphinx-data')

POCKETSPHINX_LOG = 'passive-listen.log'
ACOUSTIC_MODEL = 'pocketsphinx-data/fra-FRA/acoustic-model/' 
LANGUAGE_MODEL =  'pocketsphinx-data/fra-FRA/language-model.lm.bin'
POCKET_DICT =  'pocketsphinx-data/fra-FRA/pronounciation-dictionary.dict'
WAKE_UP_WORD = "tuxdroid"


def init():
    # Create a decoder with certain model
    config = Decoder.default_config()
    config.set_string('-logfn', POCKETSPHINX_LOG)
    config.set_string('-hmm',   ACOUSTIC_MODEL)
    config.set_string('-lm',    LANGUAGE_MODEL)
    config.set_string('-dict',  POCKET_DICT)

    # Decode streaming data
    global decoder, p
    decoder = Decoder(config)
    decoder.set_keyphrase('wakeup', WAKE_UP_WORD)
    decoder.set_search('wakeup')
    p = pyaudio.PyAudio()

    global r
    r = speech_recognition.Recognizer()
    # r.recognize_google(settings.LANG_4CODE)


def listen_keyword():
    """
    Passively listens for the WAKE_UP_WORD string
    """
    #with tts.ignore_stderr():
    global decoder, p
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000,
                    input=True, frames_per_buffer=1024)
    stream.start_stream()
    p.get_default_input_device_info()

    print("~ Waiting to be woken up... ")
    decoder.start_utt()
    while True:
        buf = stream.read(1024)
        decoder.process_raw(buf, False, False)
        if decoder.hyp() and decoder.hyp().hypstr == WAKE_UP_WORD:
            print("QQQQQQQQQQQQ1")
            decoder.end_utt()
            return
        print("QQQQQQQQQQQQ2")
    decoder.end_utt()


