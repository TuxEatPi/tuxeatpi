from queue import Empty
import time
import logging
import threading
import multiprocessing

import hug

from tuxeatpi.aptitudes.common import Aptitude, capability
from tuxeatpi.transmission import create_transmission

class Http(Aptitude, multiprocessing.Process):
#class Http(multiprocessing.Process):

    def __init__(self, tuxdroid):
        multiprocessing.Process.__init__(self)
        Aptitude.__init__(self, tuxdroid)
#        self.logger = logging.getLogger(name="tep").getChild("http")
#        self.logger.info("Initialization")
#        self.tuxdroid = tuxdroid

        @hug.get('/')
        def root():
            """Root path function"""
            return "root"
#        def toto():
#            "FFFFFFFFFFFFFFFF"
#            return "RRR"
#        toto_int = hug.interface.HTTP({'versions': []}, toto)
#        toto_int.examples= ()
#        hug.API(__name__).http.routes['/toto'] = {'GET': {None: toto_int}}
#        hug.API(__name__).extend(something, '/something')

    def run(self):
        """Main function
        - Read arguments
        - Start web server
        """
        # curl
        # -H "Content-Type: application/json"
        # -XPOST -d '{"mod": "body", "func": "wings.move_to_position", "params": {"position": "up"}}'
        # http://127.0.0.1:8000/order
        @hug.post('/order')
        def order(mod, func, params={}, block=True):
            return self.order(mod, func, params, block)

        @hug.get('/understand_text')
        def nlu_test(text):
            return self.understand_text(text)

        # Serve in a thread
        try:
            threading.Thread(target=__hug__.http.serve).start()
        except KeyboardInterrupt:
            pass

        # Handle tasks
        Aptitude.run(self)


    def order(self, mod, func, params={}, block=True):
        self.logger.info("order: %s__%s with %s", mod, func, params)
         # Create transmission
        content = {"attributes": params}
        tmn = self.create_transmission("order", mod, func, content)
        # Wait for transmission answer
        if block:
            answer = self.wait_for_answer(tmn.id_)
            # Check if we got an answer
            if answer is None:
                self.logger.warning("No answer for tmn_id: %s", tmn.id_)
                return
            # Print answer
            return answer.content


    def understand_text(self, text, say_it=True):
        self.logger.info("understand_text: %s", text)
        # Create transmission for NLU text
        content = {"attributes": {"text": text}}
        tmn = self.create_transmission("understand_text", "nlu", "text", content)
        # Wait for transmission answer
        answer = self.wait_for_answer(tmn.id_)

        # Check if we got an answer
        if answer is None:
            self.logger.warning("No answer for tmn_id: %s", tmn.id_)
            return
        # Check confidence
        elif answer.content['confidence'] < 0.8:
            self.logger.info("Text NOT understood fo tmn_id: %s", tmn.id_)
            return
        elif answer.content['confidence'] < 0.6:
            self.logger.info("Text NOT understood fo tmn_id: %s", tmn.id_)
            return
        # Get NLU answer
        mod = answer.content['mod']
        func = answer.content['func']
        content = {"attributes": answer.content['attributes']}
        # Create transmission
        tmn = self.create_transmission("understand_text", mod, func, content)
        # Wait for transmission answer
        answer = self.wait_for_answer(tmn.id_)
        # Check if we got an answer
        if answer is None:
            self.logger.warning("No answer for tmn_id: %s", tmn.id_)
            return
        # Print answer
        return answer.content


