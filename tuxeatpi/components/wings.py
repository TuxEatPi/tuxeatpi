"""
Wings component
"""

from threading import Timer
import time

try:
    from RPi import GPIO
except RuntimeError:
    # Use fake GPIO
    from GPIOSim.RPi import GPIO

from tuxeatpi.components.base import BaseComponent


class Wings(BaseComponent):
    """Define wings component
    Wings use 4 pins:
    - position:
        * INPUT
        * Help to determine wings position ('up' or 'down')
    - left_switch:
        * INPUT
        * Event when use push the left wing
    - right_switch
        * INPUT
        * Event when use push the right wing
    - movement
        * OUTPUT
        * Use to start/stop wings movement
    """

    # this will create attributes
    # - pin_position
    # - pin_left_switch
    pins = {'position': None,
            'left_switch': None,
            'right_switch': None,
            'movement': None,
            }

    def __init__(self, pins, event_queue, logger):
        BaseComponent.__init__(self, pins, event_queue, logger)
        self._setup_pins()
        # Init private attributes
        self._position = None
        self._last_time_position = None
        self._calibration_node = False
        self._wanted_position = None
        self._move_count = None

        # Setup pins
        self._setup_pins()
        # Calibrate wings position
        self._calibrate()

    def _setup_pins(self):
        """Setup all needed pings"""
        GPIO.setup(self.pins['movement'], GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(self.pins['position'], GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(self.pins['left_switch'], GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(self.pins['right_switch'], GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        # set position callback
        GPIO.add_event_detect(self.pins['position'], GPIO.RISING)
        GPIO.add_event_callback(self.pins['position'], self._position_callback)
        # set left swith callback
        GPIO.add_event_detect(self.pins['left_switch'], GPIO.RISING)
        GPIO.add_event_callback(self.pins['left_switch'], self._switch)
        # set right swith callback
        GPIO.add_event_detect(self.pins['right_switch'], GPIO.RISING)
        GPIO.add_event_callback(self.pins['right_switch'], self._switch)

    def _position_callback(self, pin_id):  # pylint: disable=W0613
        """Callback function to handle wings position
        The position is determive by the time between two
        position event (two call to this function)
        - A short time (power 5v and time < 0.3 sec)
          Means wings are UP and they are going DOWN
        - A long time (power 5v and time > 0.3 sec)
          Means wings are DOWN and they are going UP
        """
        # calibrate
        self.logger.info("Wings movement detected")
        if self._calibration_node or self._position is None:
            now = time.time()
            if self._last_time_position is not None and now - self._last_time_position > 0.1:
                if (now - self._last_time_position) > 0.3:
                    # Down - Going up
                    self._position = "down"
                else:
                    # Up - Going down
                    self._position = "up"
                self._last_time_position = now
            if self._last_time_position is None:
                self._last_time_position = now
            # TODO check the <= condition validity with real tux
            if self._move_count <= 1 and self._wanted_position == self._position:
                self._move_count = None
                self._calibration_node = False
                self.move_stop()
            else:
                self._move_count -= 1
        else:
            # Save current position
            if self._position == 'up':
                self._position = 'down'
            elif self._position == 'down':
                self._position = 'up'
            else:
                raise Exception("Unknown Error")
            # go to a wanted position
            if self._wanted_position is not None and self._position is not None:
                if self._position == self._wanted_position:
                    self._wanted_position = None
                    self.move_stop()
            # move by count
            # TODO check the <= condition validity with real tux
            elif isinstance(self._move_count, int) and self._move_count <= 1:
                self._move_count = None
                self.move_stop()

            # decrease move count if needed
            if self._move_count is not None and self._move_count > 0:
                self._move_count -= 1

    def get_position(self):
        """Return the current wings position
        and calibrate them if not available
        """
        if self._position is None:
            self._calibrate()
        return self._position

    def _calibrate(self):
        """Calibrate wings position"""
        self._calibration_node = True
        self._wanted_position = "down"
        self._move_count = 3
        self.move_start()

    def move_up(self):
        """Put wings to up position"""
        self._wanted_position = "up"
        self.move_start()

    def move_down(self):
        """Put wings to down position"""
        self._wanted_position = "down"
        self.move_start()

    def move_time(self, timeout):
        """Move wings during until timeout"""
        timer = Timer(timeout, self.move_stop)
        self.move_start()
        timer.start()

    def move_count(self, count):
        """Move wings N times"""
        self._move_count = count
        self.move_start()

    def move_start(self):
        """Start moving wings"""
        GPIO.output(self.pins['movement'], GPIO.HIGH)

    def move_stop(self):
        """Stop moving wings"""
        GPIO.output(self.pins['movement'], GPIO.HIGH)
