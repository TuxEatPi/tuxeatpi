import time

import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)

pin_id = 22

GPIO.setup(pin_id, GPIO.OUT, initial=GPIO.LOW)

#GPIO.output(pin_id, GPIO.LOW)
GPIO.output(pin_id, GPIO.HIGH)
#for i in range(3):
#	GPIO.output(pin_id, GPIO.HIGH)
#	time.sleep(2)
#	GPIO.output(pin_id, GPIO.LOW)
#	time.sleep(2)
time.sleep(5)

GPIO.cleanup()
