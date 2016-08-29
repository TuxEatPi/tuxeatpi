"""Base functions and classes for faking components"""

import time

# Use fake GPIO
import GPIOSim.RPi.in_mem as GPIO


def push_switch(pin_id):
    """Simulate switch pushing"""
    GPIO.set_pin_value(pin_id, 0)
    time.sleep(0.1)
    GPIO.set_pin_value(pin_id, 1)
