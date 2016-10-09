import uuid
import logging
import importlib
import time
import multiprocessing
import threading
from queue import Empty

from functools import wraps

from tuxeatpi.transmission import create_transmission
from tuxeatpi.libs.lang import gtt


def capability(help_text):
    def wrapper(func):
        func._is_capability = True
        func._help_text = help_text
        return func
    return wrapper

def can_transmit(func):
    @wraps(func)
    def wrapper(*args, id_=None, s_mod=None, s_func=None, **kwargs):
        text = func(*args, **kwargs)
        # Create a transmission
        if id_ is not None and s_mod is not None and s_func is not None:
            content = {"attributes": {"text": text}}
            create_transmission(s_mod, s_func, s_mod, s_func, content, id_)
        return text
    return wrapper

class Aptitude(object):
    """Class to define an Tux aptitude

    An aptitude can NOT be learnd
    """
    def __init__(self, tuxdroid):
        self._name = self.__class__.__name__
        self.logger = logging.getLogger(name="tep").getChild("aptitudes").getChild(self._name)
        self.logger.info("Initialization")
        self.dependencies = set()
        self._tuxdroid= tuxdroid
        self.settings = tuxdroid.settings
        manager = multiprocessing.Manager()
        self.answer_queue = manager.dict()
        self.task_queue = multiprocessing.Queue()
        self.answer_event_dict = manager.dict()
        self._must_run = True

    def help(self):
        raise NotImplementedError

    def push_answer(self, tmn):
        """Push an transmission answert to the current aptitude"""
        if tmn.id_ not in self.answer_event_dict:
            self.logger.warning("Transmission `%s` NOT found in answer event dict", tmn.id_)
            return
        self.logger.info("Answer received: %s", tmn.id_)
        # Put answer in answert queue
        self.answer_queue[tmn.id_] = tmn
        # Set Answer waiting flag to True
        self.answer_event_dict[tmn.id_] = True

    def push_transmission(self, task):
        """Push a transmission to the current aptitute"""
        self.task_queue.put(task)

    def create_transmission(self, source, destination, params):
        """Create a new transmission and push it to the brain"""
        tmn = create_transmission(self.__class__.__name__,
                                  s_func,
                                  mod, func, params)
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
            getattr(self, task.func)(id_=task.id_, s_mod=task.s_mod, s_func=task.s_func, **task.content['attributes'])


class Aptitudes(object):

    def __init__(self, tuxdroid):
        self.logger = logging.getLogger(name="tep").getChild("aptitudes")
        self.logger.info("Initialization")
        self.tuxdroid = tuxdroid
        self._names = set()

    def _add(self, name, aptitude):
        setattr(self, name, aptitude)
        self._names.add(name)

    def help_(self):
        aptitudes_help = {}
        for aptitude_name in self._names:
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
        # TODO get aptitude list
        aptitude_names = ["being", "hear", "http", "speak"]
        # Load modules
        for aptitude_name in aptitude_names:
            mod_aptitude = importlib.import_module('.'.join(('tuxeatpi',
                                                             'aptitudes',
                                                             aptitude_name,
                                                             aptitude_name)))
            aptitude = getattr(mod_aptitude, aptitude_name.capitalize())(self.tuxdroid)
            self._add(aptitude_name, aptitude)

    def start(self):
        self._load()
        self.logger.info("Starting")
        for aptitude_name in self._names:
            getattr(self, aptitude_name).start()

    def stop(self):
        self.logger.info("Stopping")
        for aptitude in self:
            aptitude.start()       


#class TAptitude(threading.Thread, Aptitude):
#
#    def __init__(self, intent_queue):
#        threading.Thread.__init__(self)
#        Aptitude.__init__(self, intent_queue)
#
#
#class PAptitude(multiprocessing.Process, Aptitude):
#    def __init__(self, intent_queue):
#        multiprocessing.Process.__init__(self)
#        Aptitude.__init__(self, intent_queue)
#
#
#class Intent(object):
#
#    def __init__(self, source, name, params, id_=None):
#        if len(name.split("__", 1)) != 2:
#            raise Exception("BAD Intent name")
#        self.source = source
#        self.name = name
#        self.params = params
#        if id_ is None:
#            self.id_ = uuid.uuid1()
#        else:
#            self.id_ = id_
#        self.create_time = time.time()
#
#
#def create_intent(intent_queue, source, name, params, id_=None):
#
#    # Create intent
#    new_intent = Intent(source, name, params, id_)
#
#    # Put in task queue
#    intent_queue.put(new_intent)
#
#    # return the task id
#    return new_intent.id_
#
#
#class Transmission(object):
#
#    def __init__(self, id_, source, name, params):
#        self.source = source
#        self.name = name
#        self.params = params
#        self.id_ = id_
#        self.create_time = time.time()
#
#def create_transmission(transmission_queue, source, name, params, id_=None):
#    # Create intent
#    new_intent = Transmission(source, name, params, id_)
#    # Put in task queue
#    intent_queue.put(new_intent)
#    # return the task id
#    return new_intent.id_
#
#class Response(object):
#
#    def __init__(self, id_, source, name, params):
#        self.source = source
#        self.name = name
#        self.params = params
#        self.id_ = id_
#        self.create_time = time.time()
#
#def create_response(intent_queue, source, name, params, id_=None):
#    # Create intent
#    new_intent = Intent(source, name, params, id_)
#    # Put in task queue
#    intent_queue.put(new_intent)
#    # return the task id
#    return new_intent.id_
