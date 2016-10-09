
import multiprocessing
import time
import uuid


# Transmission queue
TRANSMISSION_QUEUE = multiprocessing.Queue()


class Transmission(object):

    def __init__(self, source, destination, content, id_=None):
        if id_ is not None:
            self.id_ = id_
        else:
            self.id_ = uuid.uuid4()
        self.source = source
        self.destination = destination
        self.content = content
        self.create_time = time.time()

    def check_content(self):
        keys = ["attributes"]
        for key in keys:
            if not key in self.content:
                raise Exception("Transmission Error: %s - Missing key %s", self.id_, key)


def create_transmission(s_mod, s_func, mod, func, content, id_=None):
    # Create transmission
    new_tmn = Transmission(s_mod, s_func, mod, func, content, id_)
    # Put in transmission queue
    TRANSMISSION_QUEUE.put(new_tmn)
    # return the new transmission
    return new_tmn
