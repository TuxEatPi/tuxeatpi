#!/usr/env/bin python

from tuxeatpi.tux import Tux
import time
import logging

mytux = Tux("Pi-eater", logging.DEBUG)

while mytux.wings.get_position() is None or mytux.wings._calibration_mode:
	time.sleep(1)

time.sleep(1)
