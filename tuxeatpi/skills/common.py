"""Skills common module"""
import os
import logging
import importlib
import multiprocessing
import threading

from tuxeatpi.libs.common import AbstractComponent, threaded, subprocessed, capability, can_transmit
from tuxeatpi.transmission import create_transmission


__all__ = ["threaded",
           "subprocessed",
           "capability",
           "can_transmit",
           "Skill",
           "Skills"]


class Skill(AbstractComponent):
    """Class to define an Tux skill

    An skill can be learnd
    """
    def __init__(self, settings):
        super(Skill, self).__init__()
        self.logger.info("New skill: {}".format(self._name))
        self.settings = settings

    def _get_logger(self):
        """Get logger"""
        self.logger = logging.getLogger(name="tep").getChild("skills").getChild(self._name)

    def help_(self):
        raise NotImplementedError

    # FIXME rename me
    def create_transmission(self, s_func, destination, content):
        """Create a new transmission and push it to the brain"""
        source = ".".join(["skills", self.__class__.__name__.lower(), s_func])
        tmn = create_transmission(source, destination, content)
        return tmn


class ThreadedSkill(Skill, threading.Thread):
    """Threaded skill"""

    def __init__(self, settings):
        threading.Thread.__init__(self)
        Skill.__init__(self, settings)

    def help_(self):
        raise NotImplementedError


class SubprocessedSkill(Skill, multiprocessing.Process):
    """Subprocessed skill"""

    def __init__(self, settings):
        multiprocessing.Process.__init__(self)
        Skill.__init__(self, settings)

    def help_(self):
        raise NotImplementedError

    def stop(self):
        """Stop the process"""
        self.terminate()
        Skill.stop(self)


class Skills(object):
    """Class to handle skills"""

    def __init__(self, settings):
        self.logger = logging.getLogger(name="tep").getChild("skills")
        self.logger.info("Initialization")
        self.settings = settings
        self._names = set()

    def _add(self, name, skill):
        """Add skill to skills list"""
        setattr(self, name, skill)
        self._names.add(name)

    # TODO improve me
    def help_(self):
        """Skills help"""
        skills_help = {}
        for skill_name in self._names:
            # Get skill object
            skill = getattr(self, skill_name)
            # List attributes of skill object
            for attr_name in dir(skill):
                # List attributes of skill object
                attr = getattr(skill, attr_name, None)
                # Check if the attribute is a capability
                if getattr(attr, '_is_capability', False):
                    skill_key = ".".join(("skills", skill_name, attr_name))
                    skills_help[skill_key] = attr._help_text
        return skills_help

    def _load(self):
        """Load skills"""
        # Get skill list
        skill_names = []
        skills_dir = os.path.dirname(__file__)
        for file_name in os.listdir(skills_dir):
            abs_file_name = os.path.join(skills_dir, file_name)
            if os.path.isdir(abs_file_name):
                if "__init__.py" in os.listdir(abs_file_name):
                    skill_names.append(file_name)
        # Load modules
        for skill_name in skill_names:
            mod_skill = importlib.import_module('.'.join(('tuxeatpi',
                                                          'skills',
                                                          skill_name,
                                                          skill_name)))
            skill = getattr(mod_skill, skill_name.capitalize())(self.settings)
            self._add(skill_name, skill)

    def start(self):
        """Start all skills"""
        self._load()
        self.logger.info("Starting")
        for skill_name in self._names:
            getattr(self, skill_name).start()

    def stop(self):
        """Stop all skills"""
        self.logger.info("Stopping")
        for skill_name in self._names:
            getattr(self, skill_name).stop()
