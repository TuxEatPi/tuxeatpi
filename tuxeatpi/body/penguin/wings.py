"""Wings component"""

from threading import Timer
import time

try:
    from RPi import GPIO
except (RuntimeError, ImportError):
    # Use fake GPIO
    import GPIOSim.RPi.in_mem as GPIO

from tuxeatpi.body.common import BaseComponent, capability, can_transmit
from tuxeatpi.libs.lang import gtt


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

    def __init__(self, settings):
        BaseComponent.__init__(self, settings['pins']['wings'])
        # Init private attributes
        self._position = None
        self._last_time_position = None
        self._calibration_mode = False
        self._wanted_position = None
        self._move_count = None
        self.is_moving = False

        # Setup pins
        self._setup_pins()
        # Calibrate wings position
        self._calibrate()

    def help_(self):
        """Return wings help"""
        return gtt("Move my wings")

    def _setup_pins(self):
        """Setup all needed pings"""
        self.logger.debug("Settings Wings pins")
        GPIO.setup(self.pins['movement'], GPIO.OUT, initial=GPIO.LOW)
        for pin_name, callback in [('position', self._position_callback),
                                   ('left_switch', self._switch),
                                   ('right_switch', self._switch),
                                   ]:
            # set pin input detection
            GPIO.setup(self.pins[pin_name], GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
            try:
                GPIO.add_event_detect(self.pins[pin_name], GPIO.RISING)
                GPIO.add_event_callback(self.pins[pin_name], callback)
            except RuntimeError as exp:
                self.logger.warning("Pin {}: {}".format(self.pins[pin_name], exp))

    def _position_callback(self, pin_id):  # pylint: disable=W0613
        """Callback function to handle wings position
        The position is determive by the time between two
        position event (two call to this function)
        - A short time (power 5v and time < 0.3 sec)
          Means wings are UP and they are going DOWN
        - A long time (power 5v and time > 0.3 sec)
          Means wings are DOWN and they are going UP
        """
        # Remove bad detection
        now = time.time()
        if self._last_time_position is not None and now - self._last_time_position < 0.1:
            return
        # first dectection
        elif self._last_time_position is None:
            self._last_time_position = now
            return
        # Report good detection
        self.logger.debug("Wings movement detected")
        if self._calibration_mode or self._position is None:
            # calibration
            # Determine up or down position based on time
            if self._last_time_position is not None and now - self._last_time_position > 0.1:
                if (now - self._last_time_position) > 0.3:
                    # Down - Going up
                    self._position = "down"
                else:
                    # Up - Going down
                    self._position = "up"
                self._last_time_position = now
            # Stop calibration if our move count is 1 or less
            # And position wanted is ok
            if self._move_count <= 1 and self._wanted_position == self._position:
                self.move_stop()
                self.logger.debug("Wings calibration completed")
                return
            # Decrease the number of count
            self._move_count -= 1
        else:
            # Save current position
            if self._position == 'up':
                self._position = 'down'
            elif self._position == 'down':
                self._position = 'up'
            else:
                raise WingsError("Unknown Error")
            # Are we to a wanted position
            # Here self._position can not be None (see an if condition above)
            if self._position == self._wanted_position:
                self.move_stop()
                self.logger.debug("Wings positionning done")
            # Move by count
            # Stop move if our move count is 1 or less
            elif isinstance(self._move_count, int) and self._move_count <= 1:
                self.logger.debug("Wings moving count done")
                self.move_stop()
                return

            # decrease move count if needed
            elif isinstance(self._move_count, int) and self._move_count > 1:
                self._move_count -= 1

    @capability("Give you the position of my wings")
    @can_transmit
    def get_position(self):
        """Return the current wings position
        and calibrate them if not available
        """
        self.logger.debug("Getting wings position")
        if self._position is None and self._calibration_mode is False:
            self._calibrate()

        if self._position == "up":
            tts = gtt("My wings are up")
        elif self._position == "down":
            tts = gtt("My wings are down")
        else:
            raise WingsError("Bad wings position")
        return {"tts": tts, "result": {"position": self._position}}

    def _calibrate(self):
        """Calibrate wings position"""
        self.logger.debug("Wings calibration starting")
        self._calibration_mode = True
        self._wanted_position = "down"
        self._move_count = 3
        self.move_start()
        # Wait for calibration
        while self._calibration_mode is True:
            time.sleep(0.5)
            # TODO add timeout
            self.logger.debug("Waiting for wings calibration")
        self.logger.debug("Wings calibration done")

    @capability("Move up or move down my wings")
    @can_transmit
    def move_to_position(self, position):
        """Put wings to up position"""
        if position not in ["up", "down"]:
            raise WingsError("Bad position {}: should be 'up' or 'down'".format(position))
        self._wanted_position = position
        self.logger.debug("Putting Wings to {} position".format(position))
        self.move_start()

        if position == "up":
            tts = gtt("I'm putting my wings up")
        elif position == "down":
            tts = gtt("I'm putting my wings down")
        else:
            raise WingsError("Bad wings position")

        return {"tts": tts, "result": {"position": position}}

    @capability("Move up down my wings")
    @can_transmit
    def move_to_position_up(self):
        """Move wings to up position"""
        return self.move_to_position("up")

    @capability("Move up my wings")
    @can_transmit
    def move_to_position_down(self):
        """Move wings to down position"""
        return self.move_to_position("down")

    def move_time(self, timeout):
        """Move wings during until timeout"""
        timer = Timer(timeout, self.move_stop)
        self.logger.debug("Set Wings movement for {} seconds".format(timeout))
        self.move_start()
        timer.start()

    @capability("Move my wings X number of times")
    @can_transmit
    def move_count(self, count):
        """Move wings N times"""
        self._move_count = count
        self.logger.debug("Set Wings movement for {} times".format(self._move_count))
        self.move_start()
        tts = gtt("My wings are moving")
        return {"tts": tts, "result": {"wings": "starting"}}

    @capability("Start moving my wings")
    @can_transmit
    def move_start(self):
        """Start moving wings"""
        self.logger.debug("Wings movement starting")
        self.is_moving = True
        GPIO.output(self.pins['movement'], GPIO.HIGH)
        tts = gtt("My wings are moving")
        return {"tts": tts, "result": {"wings": "starting"}}

    @capability("Stop moving my wings")
    @can_transmit
    def move_stop(self):
        """Stop moving wings"""
        self.logger.debug("Wings movement stopping")
        self._move_count = None
        self._wanted_position = None
        self._calibration_mode = False
        self.is_moving = False
        GPIO.output(self.pins['movement'], GPIO.LOW)
        tts = gtt("My wings are stopped")
        return {"tts": tts, "result": {"wings": "stopped"}}


class WingsError(Exception):
    """Base class for wings exceptions"""
    pass
