"""Tranmission module contains tools for components communication"""

import multiprocessing
import time
import uuid


# Transmission queue
TRANSMISSION_QUEUE = multiprocessing.Queue()


class Transmission(object):
    """Transmission object is a message using to
    communicate between module/capabilities
    """

    def __init__(self, source, destination, content, id_=None):
        if id_ is not None:
            self.id_ = id_
        else:
            self.id_ = uuid.uuid4()
        self.source = source
        self.destination = destination
        self.content = content
        self.create_time = time.time()

    def check_validity(self):
        """Check the transmission content validity"""
        if not isinstance(self.content, dict):
            raise TransmissionError("Transmission Error: content is not a dict")

        if self.source == self.destination:
            keys = set(("result", "error", "tts"))

            if not keys.intersection(set(self.content.keys())):
                raise TransmissionError("Transmission Error: %s - Missing one of the "
                                        "following keys: 'data', 'error', 'tts'", self.id_)
        elif self.source != self.destination:
            if "arguments" not in self.content.keys():
                raise TransmissionError("Transmission Error: %s - Missing one of the "
                                        "following key: 'arguments'", self.id_)

    def __repr__(self):
        return ("<tuxeatpi.transmission.Transmission {} - {} => {} with "
                "{}".format(self.id_, self.source, self.destination, self.content))


def create_transmission(source, destination, content, id_=None):
    """Create a new transmission and put it in the transmission brain queue"""
    # Create transmission
    new_tmn = Transmission(source, destination, content, id_)
    # Put in transmission queue
    TRANSMISSION_QUEUE.put(new_tmn)
    # return the new transmission
    return new_tmn


class TransmissionError(Exception):
    """Base class for transmission exceptions"""
    pass
