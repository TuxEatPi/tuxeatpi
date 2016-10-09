import uuid

import threading
import select
import logging
from queue import Empty
import time


from tuxeatpi.aptitudes.speak.speak import Speak
from tuxeatpi.brain.nlu.text import NLUText
from tuxeatpi.aptitudes.being.being import Being
from tuxeatpi.skills.clock import Clock
from tuxeatpi.body.body import Body

from tuxeatpi.transmission import TRANSMISSION_QUEUE as TMN_QUEUE


class Brain(threading.Thread):

    def __init__(self, tuxdroid):
        threading.Thread.__init__(self)
        self.tuxdroid = tuxdroid
        self.settings = tuxdroid.settings

        self.logger = logging.getLogger(name="tep").getChild("brain")

        self._must_run = True

        # Init nlu text
#        self.nlu_queue_task = multiprocessing.Queue()
#        self.nlu_dict_done = multiprocessing.Manager()
        self.nlu_text = NLUText(self.settings)
        self.nlu_text.start()

#        self.body = Body()
#        self.body.start()
#        self.being = Being()
#        self.being.start()
#        self.http = Http()
#        self.http.start()
#        self.speak = Speak()
#        self.speak.start()

    def understand_text(self, text):
        self.logger.info("Trying to understand text: %s", text)
        id_ = uuid.uuid1()
        self.nlu_text.queue_task.put((id_, text))

        self.logger.info("Creating waiting event for nlu_text: %s", id_)
        self.nlu_text.task_done_dict.setdefault(id_, False)
        self.logger.info("Waiting for nlu_text: %s", id_)
        # Waiting for answer waiting flag to True
        timeout = 1
        while self.nlu_text.task_done_dict[id_] is False and timeout > 0:
            time.sleep(0.1)
            timeout -= 0.1
        # Check if we got a timeout
        if timeout < 0:
            # or critical ?
            self.logger.warning("No answer received for nlu_text: %s", id_)
            # No answer
            return None
        else:
            answer = self.nlu_text.task_done_dict.pop(id_)
            return answer

        # Wait for answer
        # TODO Return !
#        return nlu_text(self.settings, text)

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
        self._must_run = False

    def help_(self):
        capabilities_help = {}
        capabilities_help.update(self.tuxdroid.aptitudes.help_())
        return capabilities_help

    def run(self):
        timeout = 1
        while self._must_run:
            try:
                tmn = TMN_QUEUE.get(timeout=1)
            except Empty:
                continue
            self.logger.info("Transmission: %s", tmn)
            # Check params structure
            tmn.check_content()

            # Transmission for Body 
            if tmn.mod.lower() == body:
                module = self.tuxdroid.body
            # Transmission for an Aptitude
            elif hasattr(self.tuxdroid.aptitudes, tmn.mod.lower()):
                module = getattr(self.tuxdroid.aptitudes, tmn.mod.lower())
            # Transmission for an Skills
            elif hasattr(self.tuxdroid.skills, tmn.mod.lower()):
                module = getattr(self.tuxdroid.skills, tmn.mod.lower())
            elif not hasattr(self, tmn.mod.lower()):
                self.logger.critical("Module %s NOT found", tmn.mod.lower())
                tmn.mod = tmn.s_mod
                tmn.func = tmn.s_func
                module = getattr(self, tmn.mod.lower())
                module.push_answer(tmn)
            # check context/states
            # Check tmn mod/func/s_mod/s_func
            # get module
#            module = getattr(self, tmn.mod.lower())
            # Check if this is an answer
            if tmn.s_mod == tmn.mod and tmn.s_func == tmn.func:
                # Send ansert to module
                self.logger.info("Put answer %s to %s", tmn.id_, tmn.mod)
                module.push_answer(tmn)
            else:
                # Send task to module
                module.push_transmission(tmn)
                self.logger.info("Put transmission %s to %s", tmn.id_, tmn.mod)

#            inputs, _, _ = select.select([TMN_QUEUE._reader],[],[], 1)
#            if len(inputs) == 0:
#                continue
#            for input_ in inputs:
#                element = input_.recv()
