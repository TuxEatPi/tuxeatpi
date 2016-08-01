import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)

# switch
pin_id = 17
#motor
pin2_id = 22

GPIO.setup(pin2_id, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(pin_id, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

GPIO.output(pin2_id, GPIO.LOW)

GPIO.add_event_detect(pin_id, GPIO.RISING)

def toto(kwargs):
	print "GO"
	time.sleep(1)
	GPIO.setup(pin2_id, GPIO.OUT, initial=GPIO.LOW)
	GPIO.output(pin2_id, GPIO.HIGH)
	time.sleep(2)
	GPIO.output(pin2_id, GPIO.LOW)
	print "STOP"


GPIO.add_event_callback(pin_id, toto)


import time

time.sleep(60)
GPIO.cleanup()

