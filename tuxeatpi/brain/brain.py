"""TuxDroid brain module"""

import threading
import logging
import copy
from queue import Empty


from tuxeatpi.settings import SettingsError
from tuxeatpi.transmission import TRANSMISSION_QUEUE as TMN_QUEUE
from tuxeatpi.transmission import TransmissionError, create_transmission
from tuxeatpi.libs.common import capability, can_transmit, threaded
from tuxeatpi.libs.lang import gtt


class Brain(threading.Thread):
    """TuxDroid brain route transmissions to capabilities"""

    def __init__(self, tuxdroid):
        threading.Thread.__init__(self)
        self.tuxdroid = tuxdroid
        self.settings = tuxdroid.settings

        self.logger = logging.getLogger(name="tep").getChild("brain")

        self._must_run = True

    def update_setting(self, settings):
        """Update settings and save it on disk

        If new settings are bad, old settings are keeped
        and the function returns False

        Otherwise, its returns True and use new ones
        """
        self.logger.debug("Updating settings")
        old_settings = copy.copy(self.settings)
        self.settings.update(settings)
        try:
            self.logger.debug("Update settings OK")
            self.settings.save()
            return True
        except SettingsError:
            self.settings.update(old_settings)
            self.logger.debug("Update settings Failed")
            return False

    def stop(self):
        """Stop brain"""
        self._must_run = False
        TMN_QUEUE.close()

    def help_(self):
        """Return capabilities help"""
        capabilities_help = {}
        capabilities_help.update(self.tuxdroid.aptitudes.help_())
        return capabilities_help

    @capability(gtt("Give my capabilities"))
    @threaded
    @can_transmit
    def capabilities(self):
        """Capability to return capabilities list"""
        texts = []
        # Aptitudes
        caps = {}
        for cap in ["aptitudes", "skills"]:
            caps[cap] = {}
            element_names = getattr(self.tuxdroid, cap)._names
            for element_name in element_names:
                try:
                    help_text = getattr(getattr(self.tuxdroid, cap), element_name).help_()
                    if help_text is not None:
                        caps[cap][element_name] = help_text
                        texts.append(gtt("I can {}").format(help_text))
                except NotImplementedError:
                    pass
                except TypeError:
                    pass
        # Skills
        text = ". ".join(texts)
        return {"tts": text, "result": {"capabilities": caps}}

    def run(self):
        """Brain main loop"""
        timeout = 1
        while self._must_run:
            try:
                tmn = TMN_QUEUE.get(timeout=timeout)
            except Empty:
                continue
            except OSError:
                continue
            self.logger.info("Transmission: %s", tmn)
            try:
                # Check params structure
                tmn.check_validity()
            except TransmissionError as exp:
                # TODO CREATE ERROR TRANSMISSION
                self.logger.critical("Transmission %s: %s", tmn.id_, exp)
                continue

            # looking for module
            module_names = tmn.destination.split(".")[:2]
            module = self.tuxdroid
            bad_capabilities = False
            for module_name in module_names:
                if not hasattr(module, module_name.lower()):
                    self.logger.critical("No module found %s.%s",
                                         module.__class__.__name__,
                                         module_name.lower())
                    # This is not a capability
                    bad_capabilities = True
                    continue
                module = getattr(module, module_name.lower())
            # This is not a capability
            if bad_capabilities:
                self.logger.critical("Transmission %s: Destination %s is "
                                     "not a capability", tmn.id_, tmn.destination)
                # Create error transmission
                content = {"error": "`{}` is not a capability".format(tmn.destination),
                           "tts": gtt("I don't have this capability")}
                create_transmission(tmn.source, tmn.source, content, tmn.id_)
                continue

            # Check if this is an answer
            if tmn.source == tmn.destination:
                # Send ansert to module
                self.logger.info("Put answer %s to %s", tmn.id_, tmn.source)
                module.push_answer(tmn)
            elif tmn.destination.startswith("brain."):
                # Brain capacity
                self.logger.info("Transmission %s: Call brain capacity `%s`",
                                 tmn.id_,
                                 tmn.destination)
                # Call brain method
                module(id_=tmn.id_, source=tmn.source, **tmn.content['arguments'])
            else:
                self.logger.info("Put transmission %s to %s", tmn.id_, tmn.destination)
                module.push_transmission(tmn)
