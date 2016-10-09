from queue import Empty
import multiprocessing

from tuxeatpi.aptitudes.common import Aptitude, capability
from tuxeatpi.transmission import create_transmission


class Speak(Aptitude, multiprocessing.Process):

    def __init__(self, settings):
        Aptitude.__init__(self, settings)
        multiprocessing.Process.__init__(self)

    @capability
    def say(self, text):
        """Say text"""
        print("SAY, {}".format(text))
