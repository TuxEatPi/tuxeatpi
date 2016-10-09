import uuid
import logging
import time
import multiprocessing
import threading

class Skill(object):
    def __init__(self, tmn_queue):
        self._name = self.__class__.__name__
        self.logger = logging.getLogger(name="tep").getChild("skill").getChild(self._name)
        self.logger.info("New skill: {}".format(self._name))
        self.tmn_queue = tmn_queue
        self.task_queue = multiprocessing.Queue()
        self.dependencies = set()
        self._must_run = True

    def add_transmission(self, transmission):
        self.tmn_queue.put(transmission)

    def stop(self):
        self._must_run = False

    def run(self):
        while self._must_run:
            try:
                task = self.task_queue.get(timeout=1)
            except Empty:
                continue
            getattr(self, task.name)(task.id_, task.source, **task.params)
            task.done()


class SkillThread(threading.Thread, Skill):

    def __init__(self, tmn_queue):
        threading.Thread.__init__(self)
        Skill.__init__(self, tmn_queue)


class SkillProcess(multiprocessing.Process, Skill):
    def __init__(self, tmn_queue):
        multiprocessing.Process.__init__(self)
        Skill.__init__(self, tmn_queue)
