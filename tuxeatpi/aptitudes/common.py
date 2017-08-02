"""Common module for aptitudes"""

import os
import logging
import importlib
import threading
import multiprocessing


from tuxeatpi.aptitudes.birth import check_birth
from tuxeatpi.libs.common import AbstractComponent, threaded, subprocessed, capability, can_transmit


__all__ = ["threaded",
           "subprocessed",
           "capability",
           "can_transmit",
           "Aptitude",
           "Aptitudes"]


class Aptitude(AbstractComponent):
    """Class to define an Tux aptitude

    An aptitude can NOT be learnd
    """
    def __init__(self, tuxdroid):
        super(Aptitude, self).__init__()
        self._tuxdroid = tuxdroid
        self.settings = tuxdroid.settings

    def _get_logger(self):
        """Get logger"""
        self.logger = logging.getLogger(name="tep").getChild("aptitudes").getChild(self._name)

    def help_(self):
        raise NotImplementedError


class ThreadedAptitude(Aptitude, threading.Thread):
    """Threaded aptitude"""

    def __init__(self, tuxdroid):
        threading.Thread.__init__(self)
        Aptitude.__init__(self, tuxdroid)

    def help_(self):
        raise NotImplementedError


class SubprocessedAptitude(Aptitude, multiprocessing.Process):
    """Subprocessed aptitude"""

    def __init__(self, tuxdroid):
        multiprocessing.Process.__init__(self)
        Aptitude.__init__(self, tuxdroid)
        self.name = self._name

    def help_(self):
        raise NotImplementedError

    def stop(self):
        """Stop the process"""
        self.terminate()
        Aptitude.stop(self)


class Aptitudes(object):
    """Class to handle aptitudes"""

    def __init__(self, tuxdroid):
        self.logger = logging.getLogger(name="tep").getChild("aptitudes")
        self.logger.info("Initialization")
        self.tuxdroid = tuxdroid
        self.names = set()
        self.birth = False

    def _add(self, name, aptitude):
        """Add aptitude to aptitudes list"""
        setattr(self, name, aptitude)
        self.names.add(name)

    # TODO improve me
    def help_(self):
        """Aptitudes help"""
        aptitudes_help = {}
        for aptitude_name in self.names:
            # Get aptitude object
            aptitude = getattr(self, aptitude_name)
            # List attributes of aptitude object
            for attr_name in dir(aptitude):
                # List attributes of aptitude object
                attr = getattr(aptitude, attr_name, None)
                # Check if the attribute is a capability
                if getattr(attr, '_is_capability', False):
                    aptitude_key = ".".join(("aptitudes", aptitude_name, attr_name))
                    aptitudes_help[aptitude_key] = attr._help_text
        return aptitudes_help

    def _load(self):
        """Load aptitudes"""
        # Get aptitude list
        aptitude_names = []
        if self.birth and False:
            aptitude_names = ['birth', 'http']
        else:
            aptitudes_dir = os.path.dirname(__file__)
            for file_name in os.listdir(aptitudes_dir):
                abs_file_name = os.path.join(aptitudes_dir, file_name)
                if os.path.isdir(abs_file_name):
                    if "__init__.py" in os.listdir(abs_file_name):
                        print(abs_file_name)
                        aptitude_names.append(file_name)
        # Load modules
        # aptitude_names = ['speak', 'nlu', 'hear', 'being', 'http']
        for aptitude_name in aptitude_names:
            mod_aptitude = importlib.import_module('.'.join(('tuxeatpi',
                                                             'aptitudes',
                                                             aptitude_name,
                                                             aptitude_name)))
            aptitude = getattr(mod_aptitude, aptitude_name.capitalize())(self.tuxdroid)
            self._add(aptitude_name, aptitude)

    def start(self):
        """Start all aptitudes"""
        # Check birth status
        self.birth = check_birth(self.tuxdroid)
        self._load()
        self.logger.info("Starting")
        for aptitude_name in self.names:
            getattr(self, aptitude_name).start()

    def stop(self):
        """Stop all aptitudes"""
        self.logger.info("Stopping")
        for aptitude_name in self.names:
            getattr(self, aptitude_name).stop()
