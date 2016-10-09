import logging
from queue import Queue, Empty
import threading


class Body(threading.Thread):

    def __init__(self, shape, fake=False):
        threading.Thread.__init__(self)
        self._name = self.__class__.__name__
        self.logger = logging.getLogger(name="tep").getChild("body")
        sdgsadg
        self.logger.info("Body starting with shape: %s", shape)
        self._must_run = True
        self.answer_queue = {}
        self.task_queue = Queue()
        self.answer_event_dict = {}
        self._must_run = True
        # Load body components
        self._load_components()

    def _load_components(self):
        raise NotImplementedError

    def push_answer(self, tmn):
        """Push an transmission answert to the current aptitude"""
        if tmn.id_ not in self.answer_event_dict:
            self.logger.warning("Transmission `%s` NOT found in answer event dict", tmn.id_)
            return
        self.answer_queue[tmn.id_] = tmn
        self.answer_event_dict[tmn.id_].set()

    def push_transmission(self, task):
        """Push a transmission to the current aptitute"""
        self.task_queue.put(task)

    def create_transmission(self, s_func, mod, func, params):
        """Create a new transmission and push it to the brain"""
        tmn = create_transmission(self.__class__.__name__,
                                  s_func,
                                  mod, func, params)
        return tmn

    def wait_for_answer(self, tmn_id, timeout=5):
        """Blocking wait for a transmission answer on the current aptitude"""
        self.logger.info("Creating waiting event for transmission: %s", tmn_id)
        self.answer_event_dict[tmn_id] = multiprocessing.Event()
        self.logger.info("Waiting for transmission: %s", tmn_id)
        ret = self.answer_event_dict[tmn_id].wait(timeout)
        if ret is False:
            # or critical ?
            self.logger.warning("No answer received for transmission: %s", tmn_id)
            # No answer
            return None
        else:
            self.answer_event_dict.pop(tmn_id)
            answer = self.answer_queue.pop(tmn_id)
            return answer

    def stop(self):
        """Stop The current Aptitude"""
        self.logger.info("Stopping")
        self._must_run = False

    def run(self):
        """Default run loop for aptitude"""
        self.logger.info("Starting")
        while self._must_run:
            try:
                task = self.task_queue.get(timeout=1)
            except Empty:
                continue
            getattr(self, task.func)(task.id_, task.s_mod, task.s_func, **task.content['attributes'])
