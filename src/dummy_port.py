from datetime import datetime, timedelta
from random import randint
from time import sleep
from threading import Thread

import logging  
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

class DummyPort:
    """A Dummy port that acts like the real thing but instead of lighting an led 
    it just writes to the terminal. Use the function "make_activity" to simulate
    an activity signal.
    """

    def __init__(self, port_number):
        self.port_number = port_number
        self.activity_timestamp = datetime.now() - timedelta(minutes=10) # arbitrary time in the past. 
        self.cooldown_time = timedelta(seconds=5)
        self._light_duty_cycle = 0
        self._last_light_print = 0

        #start a thread that randomly picks boxes at random times. Turning this on can bu usefull for testing
#        Thread(target=self._pir_dummy_thread, daemon=True).start()  #

        self.activity_callback = None


    @property
    def activity(self):
        return datetime.now() < self.activity_timestamp + self.cooldown_time

    @property
    def time_since_activity(self):
        return datetime.now() - self.activity_timestamp

    def set_light(self, duty_cycle):
        """Set the light level of the port. 

        Args:
            duty_cycle (float): The brightness value of the led. Set between 0 and 100.
        """
        self._light_duty_cycle = duty_cycle
        # The dummy port just print the light level in the terminal for every 20 step
        # just to slow down the prints in terminal
        if abs(self._last_light_print - duty_cycle) >= 10:
            self._last_light_print = duty_cycle
            logger.info("The light on port: {} is set set to: {}".format(self.port_number, self._light_duty_cycle))
    
    def get_light(self) -> int:
        """Get the current light level

        Returns:
            int: lightlevel in percent
        """
        return self._light_duty_cycle
    
    def make_activity(self):
        """Simulate activity on the sensor pin"""
        self.activity_timestamp = datetime.now()
        if self.activity_callback is not None:
            self.activity_callback(self.port_number)  


    def set_activity_callback(self, activity_callback):
        """Set a callback for when there is activity on the port

        Args:
            Activity_callback (function(int: port_number)): The function to call when there is activity on the port. 
            The callback will receive the port number.

        Raises:
            TypeError: callback is not a callable function
        """
        if not callable(activity_callback):
            raise TypeError('callback must be callable')
        self.activity_callback = activity_callback

    def _pir_dummy_thread(self):
        """A thread that can be started to randomly make activity"""
        while True:
            sleep(randint(5, 60))
            logger.info("activity on: {}".format(self.port_number))
            self.activity_timestamp = datetime.now()
            self.make_activity()
