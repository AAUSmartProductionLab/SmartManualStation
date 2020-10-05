from dummy_port import DummyPort as Port
from typing import List
import coloredlogs, logging
from time import sleep
from threading import Thread

class PortState:
    def __init__(self,port_number):
        self.port_number = port_number
        self.selected = False
        self.amount_to_pick = 0
        self.content = None


class PickByLight:

    def __init__(self,ports: List[Port]):
        tmp_ports = self._port_sterilizer(ports)
        # create dict of all the port objects for the rack.
        self._ports = {port.port_number : port for port in tmp_ports}
        self._ports_state = {port_number : PortState(port_number) for port_number in self._ports.keys()}
        self._set_callbacks()
        self._warning_signalers = []
        self._signalers = []

    def select_port(self, port_number, amount = 1):
        if port_number not in self._ports.keys():
            logging.error('port number {} does not exist'.format(port_number))
            return
        
        if amount <= 0: 
            logging.error('Cannot pick negative or zero amount')
            return
        
        self._ports_state[port_number].selected = True
        self._ports_state[port_number].amount_to_pick = amount
        Thread(target=self._signal_thread, args=(port_number,), daemon=True).start()

    def deselect_port(self, port_number):
        if port_number not in self._ports.keys():
            logging.error('port number {} does not exist'.format(port_number))
            return

        self._ports_state[port_number].selected = False
        self._ports_state[port_number].amount_to_pick = 0

    def get_port_state(self, port_number):
        if port_number not in self._ports.keys():
            logging.error('port number {} does not exist'.format(port_number))
            return None
        return self._ports_state[port_number]  



    def _activity_callback(self,port_number):
        if self._ports_state[port_number].selected:
            self._ports_state[port_number].selected = False
            self._ports_state[port_number].amount_to_pick -= 1
        else:
            Thread(target=self._warning_signal_thread,daemon=True,args=(port_number,)).start()   

    def _port_sterilizer(self, ports):        
        for port in ports:
            if type(port) != Port:
                raise TypeError("Expected a list of ports or port numbers but got: ", type(port), port)
        return ports
    
    def _set_callbacks(self):
        for port_number, port in self._ports.items():
            port.set_activity_callback(self._activity_callback)

    def _warning_signal_thread(self, port_number):
        if port_number in self._warning_signalers:
            logging.debug('tried to spawn _warning_signal_thread but port number {} was already running'.format(port_number))
            return
        self._warning_signalers.append(port_number)
        for i in range(5):
            self._ports[port_number].set_light(True)
            sleep(0.1)  
            self._ports[port_number].set_light(False)
            sleep(0.5)

        self._ports[port_number].set_light(False)
        self._warning_signalers.remove(port_number)
    
    def _signal_thread(self,port_number):
        if port_number in self._signalers:
            logging.debug('tried to spawn _signal_thread but port number {} was already running'.format(port_number))
            return
        self._signalers.append(port_number)
        while self._ports_state[port_number].selected == True:
            self._ports[port_number].set_light(True)
            sleep(1)
            self._ports[port_number].set_light(False)
            sleep(0.2)
        self._ports[port_number].set_light(False)
        self._signalers.remove(port_number)


