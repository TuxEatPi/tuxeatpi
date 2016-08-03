from configparser import RawConfigParser
import tempfile
import os


WORK_DIR = os.path.join(tempfile.gettempdir(), "GPIOSim") #os.path.join(os.path.expanduser('~'), '.GPIOSim') 
WORK_FILE = os.path.join(WORK_DIR, "pins.ini")

def set_pin_value(pin, value):
    
    c = RawConfigParser()
    c.read(WORK_FILE)
    c.set(pin, "value", value)
#    c.set("pin"+str(pin),"value", str(value))
    with open(WORK_FILE, 'w') as configfile:
        c.write(configfile)
