#!/usr/env/bin python

import logging
import signal

from GPIOSim.RPi import GPIO

from tuxeatpi.tux import Tux

# Start GPIO eventer
eventer = GPIO.Eventer()
eventer.start()

# Create Tux object
mytux = Tux(log_level=logging.INFO)
#mytux.wings.move_up()


# Handle shutdown
def shutdown(signum, frame):
    print('You pressed Ctrl+C!')
    eventer.stop()
signal.signal(signal.SIGINT, shutdown)
