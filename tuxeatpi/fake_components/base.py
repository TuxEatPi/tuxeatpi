"""Base functions and classes for faking components"""

import time

# Use fake GPIO
from GPIOSim.RPi import GPIO


def set_pin_value(pin, value):
    """Simulate pin value changing
    setting pin value in GPIOSim ini file
    """
    GPIO.PARSER.read(GPIO.WORK_FILE)
    if not GPIO.PARSER.has_section(pin):
        GPIO.PARSER.add_section(pin)

    GPIO.PARSER.set(pin, "value", value)
    with open(GPIO.WORK_FILE, 'w') as configfile:
        GPIO.PARSER.write(configfile)


def push_switch(pin_id):
    """Simulate switch pushing"""
    set_pin_value(pin_id, 0)
    time.sleep(0.1)
    set_pin_value(pin_id, 1)
