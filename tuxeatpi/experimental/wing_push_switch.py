import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)

pin_id = 17

GPIO.setup(pin_id, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

GPIO.add_event_detect(pin_id, GPIO.RISING)

global last
last = 0


def toto(kwargs):
	global last
#	print "YEAH", kwargs
	now = time.time()
	if now - last > 0.1:
		print now - last
		#import ipdb;ipdb.set_trace()
		if (now - last) > 0.3:
			print "DOWN"
			print "going_up"
		else:
			print "UP"
			print "going_down"
		last = now

GPIO.add_event_callback(pin_id, toto)


import time

time.sleep(60)
