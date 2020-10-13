from dummy_port import DummyPort as Port
from typing import List
import logging
from time import sleep, time
from threading import Thread

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

class PortState:
    def __init__(self,port_number):
        self.port_number = port_number
        self.selected = False
        self.amount_to_pick = 0
        self.content = None


class PickByLight:

    def __init__(self,ports: List[Port]):
        # create dict of all the port objects for the rack.
        self._ports = {port.port_number : port for port in ports}
        self._ports_state = {port_number : PortState(port_number) for port_number in self._ports.keys()}
        self._set_callbacks()
        self._warning_signalers = []
        self._signalers = []

    def select_port(self, port_number, amount = 1):
        if port_number not in self._ports.keys():
            logger.error('port number {} does not exist'.format(port_number))
            return False
        
        if amount <= 0: 
            logger.error('Cannot pick negative or zero amount')
            return False
        
        self._ports_state[port_number].selected = True
        self._ports_state[port_number].amount_to_pick = amount
        Thread(target=self._signal_thread, args=(port_number,), daemon=True).start()
        return True

    def deselect_port(self, port_number):
        if port_number not in self._ports.keys():
            logger.error('port number {} does not exist'.format(port_number))
            return False

        self._ports_state[port_number].selected = False
        self._ports_state[port_number].amount_to_pick = 0
        return True
    
    def deselect_all(self):
        results = []
        for port_number in self._ports.keys():
            r = self.deselect_port(port_number)
            results.append(r)
        return all(results)

    def get_port_state(self, port_number):
        if port_number not in self._ports.keys():
            logger.error('port number {} does not exist'.format(port_number))
            return None
        return self._ports_state[port_number]  

    def get_ports(self):
        return self._ports.items()
    
    def get_port(self, port_number):
        return self._ports.get(port_number,None)

    def _activity_callback(self,port_number):
        if self._ports_state[port_number].selected:
            self._ports_state[port_number].selected = False
            self._ports_state[port_number].amount_to_pick -= 1
        else:
            Thread(target=self._warning_signal_thread,daemon=True,args=(port_number,)).start()   
    
    def _set_callbacks(self):
        for port_number, port in self._ports.items():
            port.set_activity_callback(self._activity_callback)

    def _warning_signal_thread(self, port_number):
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

        self._ports[port_number].set_light(False)
        self._warning_signalers.remove(port_number)
    
    def _signal_thread(self,port_number):
        if port_number in self._signalers:
            logger.debug('tried to spawn _signal_thread but port number {} was already running'.format(port_number))
            return
        self._signalers.append(port_number)

        port = self._ports[port_number]
        port_state = self._ports_state[port_number]

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

        port.set_light(False)
        self._signalers.remove(port_number)


