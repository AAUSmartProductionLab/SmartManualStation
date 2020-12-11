import logging
import yaml
import os
from datetime import datetime, timedelta
import RPi.GPIO as GPIO

logger = logging.getLogger(__name__) # Gives the root logger.  Change this for better organization
logger.setLevel(logging.WARNING)

GPIO.setmode(GPIO.BOARD)


class PiPort:
    """Raspberry pi port for the pick by light. Each port has a number and a sensor to detect activity. 
    The port can signal with an LED to attract attention to the port. 
    """
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
        """Classmethod: Run once to load a pinout file for all the ports. 
        The file must by in Yaml format like this:

            Connector:
                led_pin: gpio pin
                pir_pin: gpio pin

         ##### example #####
            1:
                led_pin : 35
                pir_pin : 36
            2:
                led_pin : 33
                pir_pin : 37

        Args:
            pin_conf_name (Str): relative or absolute path to the yaml file.

        Raises:
            FileNotFoundError: If the yaml file cannot be found or has problems opening
            KeyError: If the yaml file does not have the required pir_pin
        """
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
        """Classmethod: Returns the pinout for all ports on the raspberry pi. 

        Returns:
            dict: pinout for all ports
        """
        return cls.__ports_config

    @property
    def activity(self) -> bool:
        """Property: True if there is activity on the port

        Returns:
            bool: True if there is activity on the port
        """
        return datetime.now() <= self.activity_timestamp + self.cooldown_time

    @property
    def time_since_activity(self):
        return datetime.now() - self.activity_timestamp
    
    def set_light(self, duty_cycle):
        """Set the light level of the led on the port. The lightlevel is in percent and should
        between 0 and 100. Values outside this range is capped to either 0 or 100. No warning 
        is generated  if value is outside range.

        Args:
            duty_cycle (float): brightness in percent.

        Returns:
            bool: success
        """
        # limit between 0 and 100
        self._light_duty_cycle = max(min(duty_cycle, 100), 0)
        return self.light_pwm.ChangeDutyCycle(self._light_duty_cycle)
    
    def get_light(self) -> int:
        """Get the current light level

        Returns:
            int: lightlevel in percent
        """
        return self._light_duty_cycle  

    def make_activity(self):
        """Simulate activity on the sensor pin"""
        logger.info('Made activity at port: {}'.format(self.port_number))
        self._pir_callback()

    def set_activity_callback(self, activity_callback):
        """Set a callback for when there is activity on the port

        Args:
            Activity_callback (function(int: port_number)): The function to call when there is activity on the port. 
            The callback will receive the port number.

        Raises:
            TypeError: callback is not a callable function
        """
        if not callable(activity_callback):
            raise TypeError('activity_callback must be callable. You gave it type: {}'.format(type(activity_callback)))
        self.activity_callback = activity_callback

    @property
    def _led_pin(self):
        """Property: physical raspberry pi pin to controll the light.

        Returns:
            int: Physical pin number.
        """
        port_conf = PiPort.__ports_config[self.port_number]
        return port_conf.get('led_pin', None)
    
    @property
    def _pir_pin(self):
        """Property: physical raspberry pi in to sensinc activity.

        Returns:
            int: Physical sensor pin.
        """
        port_conf = PiPort.__ports_config[self.port_number]
        return port_conf.get('pir_pin')

    def _pir_callback(self,pin=None):
        """Private calback when the sensor pin is pulled high.
        This callback acts like a filter to bouncy signals.

        Args:
            pin (int): NOT USED: Physical sensor pin that pulled the signal high
        """
        # if 5 sec passed since last activity
        if datetime.now() > self.activity_timestamp + self.cooldown_time:
            print('Pir detected high at port %s' % self.port_number)
            if self.activity_callback is not None:
                self.activity_callback(self.port_number)    
            self.activity_timestamp = datetime.now()
