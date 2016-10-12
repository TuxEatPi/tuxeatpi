"""Common module for aptitudes"""

import time
import multiprocessing
import threading
from queue import Empty

from functools import wraps

from tuxeatpi.transmission import create_transmission, Transmission
# from tuxeatpi.libs.lang import gtt


def threaded(func):
    """Run a capability in a thread"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        """Wrapper function for threaded decorator"""
        threading.Thread(target=func, args=args, kwargs=kwargs).start()
    return wrapper


def subprocessed(func):
    """Run a capability in a subprocess"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        """Wrapper function for subprocessed decorator"""
        multiprocessing.Process(target=func, args=args, kwargs=kwargs).start()
    return wrapper


def capability(help_text):
    """Make method as a capability"""

    def wrapper(func):
        """Wrapper function for capability decorator"""
        func._is_capability = True
        func._help_text = help_text
        return func
    return wrapper


def can_transmit(func):
    """The capability will send to transmission in order to answer to the requester"""

    @wraps(func)
    def wrapper(*args, id_=None, source=None, **kwargs):
        """Wrapper function for can_transmit decorator"""
        content = {}
        try:
            content = func(*args, **kwargs)
        except TypeError as exp:
            # TODO create a transmission error
            content = {"error": str(exp)}
        # Create a transmission
        if id_ is not None and source is not None:
            create_transmission(source, source, content, id_)
        return content
    return wrapper


class AbstractComponent(object):
    """Abstract Class to define Tux aptitude/skill/body"""
    def __init__(self):
        self._name = self.__class__.__name__
        self.logger = None
        self._get_logger()
        self.logger.info("Initialization")
        self.dependencies = set()
        manager = multiprocessing.Manager()
        self.answer_queue = manager.dict()
        self.task_queue = multiprocessing.Queue()
        self.answer_event_dict = manager.dict()
        self._must_run = True

    def _get_logger(self):
        """Get logger"""
        raise NotImplementedError

    def help_(self):
        """Help about the aptitude"""
        raise NotImplementedError

    def push_answer(self, tmn):
        """Push an transmission answert to the current aptitude"""
        retries = 3
        while tmn.id_ not in self.answer_event_dict:
            retries -= 1
            if retries == 0:
                # TODO retry
                self.logger.warning("Transmission `%s` NOT found in answer event dict", tmn.id_)
                return
            else:
                self.logger.info("Transmission `%s` NOT found in answer event "
                                 "dict - retrying", tmn.id_)
                time.sleep(0.01)
        self.logger.info("Answer received: %s", tmn.id_)
        # Put answer in answert queue
        self.answer_queue[tmn.id_] = tmn
        # Set Answer waiting flag to True
        self.answer_event_dict[tmn.id_] = True

    def push_transmission(self, task):
        """Push a transmission to the current aptitute"""
        self.task_queue.put(task)

    # FIXME rename
    def create_transmission(self, s_func, destination, content):
        """Create a new transmission and push it to the brain"""
        source = ".".join(["aptitudes", self.__class__.__name__.lower(), s_func])
        tmn = create_transmission(source, destination, content)
        return tmn

    def wait_for_answer(self, tmn_id, timeout=5):
        """Blocking wait for a transmission answer on the current aptitude"""
        self.logger.info("Creating waiting event for transmission: %s", tmn_id)
        self.answer_event_dict.setdefault(tmn_id, False)
        self.logger.info("Waiting for transmission: %s", tmn_id)
        # Waiting for answer waiting flag to True
        while self.answer_event_dict[tmn_id] is False and timeout > 0:
            time.sleep(0.1)
            timeout -= 0.1
        # Check if we got a timeout
        if timeout < 0:
            # or critical ?
            self.logger.warning("No answer received for transmission: %s", tmn_id)
            # No answer
            content = {"error": "no answer received"}
            return Transmission(None, None, content, tmn_id)

        else:
            self.answer_event_dict.pop(tmn_id)
            answer = self.answer_queue.pop(tmn_id)
            return answer

    def stop(self):
        """Stop The current Aptitude"""
        self.logger.info("Stopping")
        self._must_run = False
        self.task_queue.close()

    def run(self):
        """Default run loop for aptitude"""
        self.logger.info("Starting")
        while self._must_run:
            try:
                task = self.task_queue.get(timeout=1)
            except Empty:
                continue
            except OSError:
                continue

            method_names = task.destination.split(".")[2:]
            method = self
            loop_end = False
            for method_name in method_names:
                method = getattr(method, method_name, None)
                if method is None:
                    # Method not found, send error transmission
                    error = "No capability found {}".format(method)
                    content = {"error": error}
                    self.logger.critical(error)
                    create_transmission(source=task.source,
                                        destination=task.source,
                                        content=content,
                                        id_=task.id_)
                    loop_end = True
            if loop_end:
                continue
            # Run the capability
            if getattr(method, '_is_capability', False):
                method(id_=task.id_, source=task.source, **task.content['arguments'])
            else:
                # Method not found, send error transmission
                error = "No capability found {}".format(method)
                content = {"error": error}
                self.logger.critical(error)
                create_transmission(source=task.source,
                                    destination=task.source,
                                    content=content,
                                    id_=task.id_)
