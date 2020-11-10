import logging
import yaml
import os
from datetime import datetime, timedelta
import RPi.GPIO as GPIO

logger = logging.getLogger(__name__) # Gives the root logger.  Change this for better organization
logger.setLevel(logging.WARNING)

GPIO.setmode(GPIO.BOARD)


class PiPort:
    __ports_config = {}

    def __init__(self,port_number):
        self.port_number = port_number
        self.activity_timestamp = datetime.now() - timedelta(minutes=10) # default is an arbitrary time in the past. 
        self.cooldown_time = timedelta(seconds=5)

        # GPIO setup
        GPIO.setup(self._pir_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(self._led_pin, GPIO.OUT)

        self.activity_callback = None
        self.light_pwm = GPIO.PWM(self._led_pin, 1000)
        self.light_pwm.start(0)
        self._light_duty_cycle = 0


        

        # Add interupt and callback function when there's a change on the pir pin. 
        GPIO.add_event_detect(self._pir_pin, GPIO.RISING, callback=self._pir_callback)
        pass
   
    @classmethod    
    def load_pinout_from_file (cls, pin_conf_name):
        try:
            root_dir = os.path.abspath(os.path.dirname(__file__))
            yaml_path = os.path.join(root_dir, pin_conf_name)
            with open(yaml_path, 'r') as conf_file:
                cls.__ports_config = yaml.safe_load(conf_file)      

        except FileNotFoundError as f:
            raise FileNotFoundError('The pin configuration file: %s, could not be found' %f)

        # loop through the pin configurations for each connector and verify the pins
        # This loop verifies all settings make sense. 
        for port, args in cls.__ports_config.items():
            # log the loaded data.
            logger.info('port {} : led_pin = {}, pir_pin = {}'.format(port, args.get('led_pin',None), args.get('pir_pin',None)))
            
            # Make sure the pins are specified.
            # Else give a warning about missing config params. 
            if 'led_pin' not in args:
                logger.warn('Port "%s" does not have an "led_pin" specified.' %port)
                
            if 'pir_pin' not in args:
                logger.error('Port "%s" does not have the mandatory key "pir_pin".' %port)
                raise KeyError('Port "%s" does not have the mandatory key "pir_pin".' %port)

    @classmethod
    def get_ports_pinout(cls):
        return cls.__ports_config

    @property
    def activity(self) -> bool:
        return datetime.now() <= self.activity_timestamp + self.cooldown_time

    @property
    def time_since_activity(self):
        return datetime.now() - self.activity_timestamp
    
    def set_light(self, duty_cycle):
        # limit between 0 and 100
        self._light_duty_cycle = max(min(duty_cycle, 100), 0)
        return self.light_pwm.ChangeDutyCycle(self._light_duty_cycle)
    
    def get_light(self) -> int:
        return self._light_duty_cycle  

    def make_activity(self):
        print('Activity at port %s' % self.port_number)
        self.activity_timestamp = datetime.now()
        self._callbacks()

    def set_activity_callback(self, activity_callback):
        if not callable(activity_callback):
            raise TypeError('activity_callback must be callable. You gave it type: {}'.format(type(activity_callback)))
        self.activity_callback = activity_callback

    @property
    def _led_pin(self):
        port_conf = PiPort.__ports_config[self.port_number]
        return port_conf.get('led_pin', None)
    
    @property
    def _pir_pin(self):
        port_conf = PiPort.__ports_config[self.port_number]
        return port_conf.get('pir_pin')

    def _pir_callback(self,pin):
        # if 5 sec passed since last activity
        if datetime.now() > self.activity_timestamp + self.cooldown_time:
            print('Pir detected high at port %s' % self.port_number)
            self._callbacks()
            self.activity_timestamp = datetime.now()

    def _callbacks(self):
        if self.activity_callback is not None:
            self.activity_callback(self.port_number)    