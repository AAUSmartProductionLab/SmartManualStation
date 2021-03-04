from dummy_port import DummyPort as Port
from typing import List
import logging
from time import sleep, time
from threading import Thread
import os
import yaml

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class PortState:
    """Descriptor for the state of a port.
    """
    # TODO this should just be a dict like the port configs and many other things in this project. 
    # This is the odd one out.
    def __init__(self,port_number):
        self.port_number = port_number
        self.selected = False
        self.work_finished = False
        self.amount_to_pick = 0
        self.select_instructions = ''


class PickByLight:
    """Controller for a bunch of ports on a pick by light setup."""

    def __init__(self,ports: List[Port], default_content_map_path = None):
        """Constructor:

        Args:
            ports (List[Port]): Hardware of type Port
            default_content_map_path (str, optional): Path to a default content map. Defaults to None.
        """
        # create dict of all the port objects for the rack.
        self._ports = {port.port_number : port for port in ports}
        self._ports_state = {port_number : PortState(port_number) for port_number in self._ports.keys()}
        self._set_callbacks()
        self._warning_signalers = []
        self._signalers = []
        self._content_map = {}

        if default_content_map_path:
            self._content_map = self.load_content_map(default_content_map_path)


    def select_port(self, port_number, amount = 1, instructions = ''):
        """Select a port with the giver port number. Instructions can be sent 
        along with the selection to instruct the worker on what to do.

        Args:
            port_number (int): Port number to be selected
            amount (int, optional): Amount to pick. Defaults to 1.
            instructions (str, optional): Instructions to be displayed for the worker. Defaults to ''.

        Returns:
            bool: success
        """
        
        if port_number not in self._ports.keys():
            logger.error('port number {} does not exist'.format(port_number))
            return False
        
        if amount <= 0: 
            logger.error('Cannot pick negative or zero amount')
            return False
        
        self._ports_state[port_number].selected = True
        self._ports_state[port_number].work_finished = False
        self._ports_state[port_number].amount_to_pick = amount
        self._ports_state[port_number].select_instructions = instructions
        Thread(target=self._signal_thread, args=(port_number,), daemon=True).start()
        return True
    
    def select_content(self, name, amount = 1, instructions = ''):
        """Select a port from the content within it. Instructions can be sent
        along with the selection to instruct the worker on what to do. 
        The first port with a matching content name will be selected.  

        Args:
            name (string): name of the content to be selected
            amount (int, optional): Amount to pick. Defaults to 1.
            instructions (str, optional): Instructions to be displayed for the worker. Defaults to ''.

        Returns:
            bool: success
            int: port number selected. returns -1 if not successful
        """
        for port_number, content in self._content_map.items():
            if content.get('name', None) == name:
                success = self.select_port(port_number, amount, instructions)
                return success, port_number
        else:
            return False, -1


    def work_finished(self,port_number):
        """Set flag that the work on this port is now done and submitted.
        This also deselects the port and turns off the light.

        Args:
            port_number (int): port number to submit work

        Returns:
            bool: success
        """
        return self.deselect_port(port_number, work_finished=True)

    def deselect_port(self, port_number, work_finished = False):
        """Deselect a port with the giver number. 

        Args:
            port_number (int): The port number to be deselected
            work_finished (bool): Is the work done or should we just turn off the led.

        Returns:
            bool: success
        """
        if port_number not in self._ports.keys():
            logger.error('port number {} does not exist'.format(port_number))
            return False

        self._ports_state[port_number].selected = False
        self._ports_state[port_number].work_finished = work_finished
        self._ports_state[port_number].amount_to_pick = 0
        self._ports_state[port_number].select_instructions = ''
        return True
    
    def deselect_content(self, name, work_finished=False):
        """Deselect a port with the giver content name. 

        Args:
            name (str): The name of the content to be deselected
            work_finished (bool): Is the work done or should we just turn off the led

        Returns:
            bool: success
            int: port number deselected. returns -1 if not successful
        """
        for port_number, content in self._content_map.items():
            if content.get('name', None) == name:
                success = self.deselect_port(port_number, work_finished)
                return success, port_number
        else:
            return False, -1
    
    def deselect_all(self):
        """Deselect and marks all ports as finished

        Returns:
            bool: success. Returns True if all ports were deselected successfully.
        """
        results = []
        for port_number in self._ports.keys():
            r = self.deselect_port(port_number=port_number, work_finished=True)
            results.append(r)
        return all(results)

    def get_port_state(self, port_number):
        """Get the state of the port

        Args:
            port_number (int): port number you want to get the state of

        Returns:
            PortState: PortState obj 
        """
        if port_number not in self._ports.keys():
            logger.error('port number {} does not exist'.format(port_number))
            return None
        return self._ports_state[port_number]  
    
    def set_port_state(self, port_number, key, value):
        """Set a value in the state obj of a port.

        Args:
            port_number (int): port number to change the state of
            key (str): state attribute to change
            value (any): value of the state attribute

        Returns:
            bool: success
        """
        if port_number not in self._ports.keys():
            logger.error('port number {} does not exist'.format(port_number))
            return False
        if not hasattr(self._ports_state[port_number], key):
            logger.error('port state has no attribute called {}'.format(key))
            return False    
        setattr(self._ports_state[port_number], key, value)
        return True

    def get_ports_state(self):
        """Get a dict with the state of all the ports

        Returns:
            dict: dict indexed by port number
        """
        return self._ports_state

    def get_ports(self):
        """Get all the port objects in this pick by light

        Returns:
            dict: dict indexed by port number
        """
        return self._ports.items()
    
    def get_port(self, port_number):
        """Get the port object by port number

        Args:
            port_number (int): port number to get the object of

        Returns:
            Port: Port object
        """
        return self._ports.get(port_number,None)
    
    def get_content(self, port_number):
        """Get the content of a port

        Args:
            port_number (int): port number to get the content of

        Returns:
            dict: dict of content info
        """
        return self._content_map.get(port_number,{})

    def get_all_contents_display_name(self):
        """Get all the display names of the content from all ports

        Returns:
            dict: dict indexed by port number
        """
        return {port_number:content.get('display_name','?') for port_number, content in self._content_map.items()}

    def get_all_contents_name(self):
        """Get all the content names of the content from all ports

        Returns:
            dict: dict indexed by port number
        """
        return {port_number:content.get('name','') for port_number, content in self._content_map.items()}

    def get_all_contents_description(self):
        """Get all the descriptions of the content from all ports

        Returns:
            dict: dict indexed by port number
        """
        return {port_number:content.get('description','') for port_number, content in self._content_map.items()}

    def get_all_contents_image_path(self):
        """Get all the image paths of the content from all ports

        Returns:
            dict: dict indexed by port number
        """
        return {port_number:content.get('image_path','') for port_number, content in self._content_map.items()}
    
    def get_all_contents_x(self,x):
        """Get all the x of the content from all ports

        Args:
            x (str): the key to get

        Returns:
            dict: dict indexed by port number
        """
        return {port_number:content.get(x,'') for port_number, content in self._content_map.items()}

    def set_content(self,port_number, content):
        """Set the content of a port

        Args:
            port_number (int): port number to change the content of
            content (dict): dict what contains name : value of the content
        """
        if port_number in self._content_map:
            if type(content) != dict:
                raise TypeError('content must be of type: dict. Instead received: {}'.format(type(content)))
            self._content_map[port_number] = content

    def set_content_key(self, port_number, key, value):
        """Set a specific attribute of the content of a port

        Args:
            port_number (int): port number to change the content of
            key (str): attribute to change
            value (any): value of the key
        """
        if port_number in self._content_map:
            self._content_map[port_number][key] = value

    def load_content_map(self,yaml_path):
        """Load a content map from file

        Args:
            yaml_path (str): path to the file, relative or absolute

        Returns:
            dict: returns the loaded content map
        """
        # absolute path
        _yaml_path = os.path.join('', yaml_path)
        if not os.path.isfile(_yaml_path):
            # try relative path
            root_dir = os.path.abspath(os.path.dirname(__file__))
            _yaml_path = os.path.join(root_dir, yaml_path)
        if not os.path.isfile(_yaml_path):
            logger.error('The content_map file: {}, could not be found. No content loaded.'.format(yaml_path))
            return {}         
           
        with open(_yaml_path, 'r') as content_file:
            content_map = yaml.safe_load(content_file)
            logger.debug('content_map ----> {0}'.format(content_map))
            self._content_map = content_map
            return content_map
    
    def save_content_map(self, yaml_path):
        """Save the current content map as a file

        Args:
            yaml_path (str): path to save location
        """
        yaml_name = os.path.basename(yaml_path)
        if not yaml_name.endswith('.yaml'):
            yaml_path += '.yaml'        
        with open(yaml_path, 'w') as outfile:
            yaml.dump(self._content_map, outfile, default_flow_style=False)

    def _activity_callback(self,port_number):
        """Callback for the ports to call when there is activity

        Args:
            port_number (int): port that had activity
        """
        if self._ports_state[port_number].selected:
            logger.info('activity on port: {} caused it do be deselected'.format(port_number))
            self.deselect_port(port_number)
        else:
            logger.info('activity on port: {} cased a warning light to be triggered because the port was not selected')
            Thread(target=self._warning_signal_thread, daemon=True, args=(port_number,)).start()   
    
    def _set_callbacks(self):
        """Sets the callback on all the ports for when an activity occurs"""
        for port_number, port in self._ports.items():
            port.set_activity_callback(self._activity_callback)

    def _warning_signal_thread(self, port_number):
        """A thread function that blinks a port led sharply where there is activity on 
        a nonselected port to warn the user that this was not correct. 
        
        This function is threadsafe meaning it is okay to call this function multiple times. Only
        one thread will be running at any one time.

        Args:
            port_number (int): port number to signal
        """
        if port_number in self._warning_signalers:
            logger.debug('tried to spawn _warning_signal_thread but port number {} was already running'.format(port_number))
            return
        self._warning_signalers.append(port_number)
        for i in range(5):
            if self._ports_state[port_number].selected: 
                break
            self._ports[port_number].set_light(100)
            sleep(0.1)  
            self._ports[port_number].set_light(0)
            sleep(0.25)

        self._ports[port_number].set_light(0)
        self._warning_signalers.remove(port_number)
    
    def _signal_thread(self,port_number):
        """Signals calmly to the user that the port is selected. 

        This function is threadsafe meaning it is okay to call this function multiple times. Only
        one thread will be running at any one time.
        
        Args:
            port_number (int): port number to signal 
        """
        if port_number in self._signalers:
            logger.debug('tried to spawn _signal_thread but port number {} was already running'.format(port_number))
            return
        self._signalers.append(port_number)

        port = self._ports[port_number]
        port_state = self._ports_state[port_number]

        # while selected
        while port_state.selected == True:
            for i in range(0, 100+1):
                port.set_light(i)
                sleep(0.005)
                if port_state.selected == False: break

            for i in range(30):
                sleep(0.1)
                if port_state.selected == False: break

            l = port.get_light()
            for i in range(l, -1, -1):
                port.set_light(i)
                sleep(0.005)
                
            for i in range(2):
                sleep(0.1)
                if port_state.selected == False: break
        
        # finally make sure the light is turned off
        port.set_light(0)

        self._signalers.remove(port_number)


