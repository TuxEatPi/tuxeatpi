"""TuxDroid module defining TuxDroid Class"""

import logging
import importlib

from tuxeatpi.brain.brain import Brain
from tuxeatpi.aptitudes.common import Aptitudes
from tuxeatpi.skills.common import Skills
from tuxeatpi.settings import Settings


class Tux(object):
    """Tux droid new life class"""
    def __init__(self, config_file):
        # Init logging
        logging.basicConfig()

        self.logger = logging.getLogger(name="tep")
        # Get settings
        self.settings = Settings(config_file, self.logger)

        # Set start time
        self.logger.debug("Starting TuxDroid named '%s'", self.settings['global']['name'])

        # Start brain
        self.brain = Brain(self)
        self.brain.start()
        # Start body
        self.body = None
        self._load_body('penguin', True)
        self.body.start()
        # Start aptitudes
        self.aptitudes = Aptitudes(self)
        self.aptitudes.start()
        # Start skills
        self.skills = Skills(self.settings)
        self.skills.start()

    def shutdown(self):
        """Shutdown the TuxDroid"""
        self.skills.stop()
        self.aptitudes.stop()
        self.body.stop()
        self.brain.stop()

    def _load_body(self, shape_name, fake=False):
        """Load the TuxDroid Body/shape"""
        # TODO get shape list
        shape_names = ["penguin"]
        if shape_name not in shape_names:
            raise Exception("Not shape %s found", shape_name)
        else:
            mod_shape = importlib.import_module('.'.join(('tuxeatpi',
                                                          'body',
                                                          shape_name,
                                                          'shape')))
            self.body = getattr(mod_shape, shape_name.capitalize())(self.settings, fake)
