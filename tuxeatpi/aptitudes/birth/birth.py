import time

from tuxeatpi.aptitudes.common import ThreadedAptitude, capability, can_transmit, threaded
#from tuxeatpi.aptitudes.birth.wf_utils import 


class Birth(ThreadedAptitude):

    def __init__(self, tuxdroid):
        ThreadedAptitude.__init__(self, tuxdroid)
        self.start_time = time.time()
        print("DDDDDDDDDDDD")


    def scan_wifi(self):
        pass
#        import ipdb;ipdb.set_trace()
