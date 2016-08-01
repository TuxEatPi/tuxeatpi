import RPi.GPIO as GPIO

from elem

PIN_IDS = [4, 22, 17]

class Wings(Element):

    # this will create attributes
    # - pin_position
    # - pin_left_switch
    pin_name_list = ['position',
                     'left_switch',
                     'right_switch',
                     'movement',
                    ]

    def __init__(self, pins):
        # Check pin_name_list validity
        if not hasattr(self, 'pin_name_list'):
            raise AttributeError("pin_name_list attribute must be defined")
        if not isinstance(self.pin_name_list, list):
            raise AttributeError("Bad attribute definition: pin_name_list")
        for pin_name in self.pin_name_list:
            if not isinstance(pin_name, str):
                raise AttributeError("Bad item definition in pin_name_list %s" % pin_name)
        # Check pins validity
        if not isinstance(pins, dict):
            raise AttributeError("Bad attribute definition: pins")
        for pin_name, pin_id in pins.items():
            if not isinstance(pin_name, str):
                raise AttributeError("Bad attribute definition: pins")
            if not isinstance(pin_id, int):
                raise AttributeError("Bad pin id for pin %s. Should be in %s" % (pin_name, PIN_IDS))
            if pin_id not in pin_ids:
                raise AttributeError("Bad pin id for pin %s. Should be in %s" % (pin_name, PIN_IDS))
        if set(pins.keys()) != set(self.pin_name_list):
            raise AttributeError("Your pin list should be %s" % self.pin_name_list)
        for pin_name1 in self.pin_name_list:
            for pin_name2 in self.pin_name_list:
                if pin_name1 != pin_name2 and pins[pin_name1] == pins[pin_name1]:
                        raise AttributeError("Bad pin definition: %s and %s are on the same pin id" % (pin_name1, pin_name2))

        # Set pins
        for pin_name in pin_name_list:
            setattr(self, "pin_" + pin_name, None)

    def _configure_pins(self):
        GPIO.setup(self.pin_movement, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(self.pin_position, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(self.pin_left_switch, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(self.pin_right_switch, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)


    def get_wings_position(self):
        if self.wings_position is None:
            self._calibrate_wings()
        return self.wings_position
 
    def _calibrate_wings(self):
        
        self.wings_position = "DOWN"

    def move_wings(self):
        pass        
