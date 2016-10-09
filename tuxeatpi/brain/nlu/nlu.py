from queue import Empty
import multiprocessing

from tuxeatpi.aptitudes.common import Aptitude
from tuxeatpi.transmission import create_transmission


class NLU(multiprocessing.Process, Aptitude):

    def __init__(self):
        multiprocessing.Process.__init__(self)
        Aptitude.__init__(self)

    def run(self):
        while self._must_run:
            try:
                task = self.task_queue.get(timeout=1)
            except Empty:
                continue
            getattr(self, task.func)(task.id_, task.s_mod, task.s_func, **task.content['attributes'])

    def text(self, id_, s_mod, s_func, text):
        dsgdsg
        self.logger.info("Id: %s - text: %s", id_, text)
        # Try to understand text
        mod = "being"
        func = "name"
        content = {"mod": mod,
                  "func": func,
                  "confidence": 0.8,
                  "attributes": {},
                  }
        # Create transmission
        tmn = create_transmission(s_mod, s_func, s_mod, s_func, content, id_=id_)
        self.logger.info("understand toto %s", tmn)
