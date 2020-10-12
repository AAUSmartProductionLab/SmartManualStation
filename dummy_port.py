from datetime import datetime, timedelta
from random import randint
from time import sleep
from threading import Thread


class DummyPort:
    def __init__(self, port_number):
        self.port_number = port_number
        self.activity_timestamp = datetime.now() - timedelta(minutes=10) # arbitrary time in the past. 
        self.cooldown_time = timedelta(seconds=5)
        self._light_duty_cycle = 0
        self._last_light_print = 0
        Thread(target=self._pir_dummy_thread, daemon=True).start()  #

        self.activity_callback = None


    @property
    def activity(self):
        return datetime.now() < self.activity_timestamp + self.cooldown_time

    @property
    def time_since_activity(self):
        return datetime.now() - self.activity_timestamp

    def set_light(self, duty_cycle):
        self._light_duty_cycle = duty_cycle
        # The dummy port just print the light level in the terminal for every 20 step
        # just to slow down the prints in terminal
        if abs(self._last_light_print - duty_cycle) >= 10:
            self._last_light_print = duty_cycle
            print("The light on port: ", self.port_number, " is set to:", self._light_duty_cycle)
    
    def get_light(self) -> int:
        return self._light_duty_cycle
    
    def make_activity(self):
        self.activity_timestamp = datetime.now()
        self._callbacks()


    def set_activity_callback(self, activity_callback):
        if not callable(activity_callback):
            raise TypeError('callback must be callable')
        self.activity_callback = activity_callback

    def _pir_dummy_thread(self):
        while True:
            sleep(randint(5, 60))
            print("activity on: ", self.port_number)
            self.activity_timestamp = datetime.now()
            self.activity_callback(self.port_number)

    def _callbacks(self):
        if self.activity_callback is not None:
            self.activity_callback(self.port_number)  


