from time import sleep
from threading import Thread, Event
from opcua import ua, Client
import socket
from pick_by_light import PickByLight

import logging  
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)


class FestoServer():
    def __init__(self, pick_by_light: PickByLight, festo_ip: str, ua_port = '4840'):
        super().__init__(daemon=True)
        self._pbl = pick_by_light

        try:
            self.client = Client("opc.tcp://{}:{}".format(festo_ip, ua_port))
            self.client.connect()
            logger.info("Festo OPC-UA Client Connected")
            self.connected = True
        except socket.timeout:
            logger.warning("Failed to connect to OPC-UA on {}:{}".format(festo_ip,ua_port))
            self.connected = False
        self._select_event = Event()
        Thread(target=self.run, daemon=True)
        
    def run(self):
        while self.connected:
            sleep(0.1)
            flag = self.client.get_node("ns=2;s=|var|CECC-LK.Application.Flexstation_globalVariables.FlexStationStatus") 
            status = flag.get_value()
            if status == 1:
                flag.set_value(ua.Variant(2, ua.VariantType.Int16))
                Operation_number = self.client.get_node("ns=2;s=|var|CECC-LK.Application.FBs.stpStopper1.stAppControl.uiOpNo").get_value() # change to order id
                Order_url = self.client.get_node("ns=2;s=|var|CECC-LK.Application.AppModul.stRcvData.sOderDes").get_value()

                port_number = self.operation_number_to_port(Operation_number,Order_url)
                while self._pbl.get_port_state(port_number).selected and status == 2:
                    sleep(0.1)
                    
                flag.set_value(ua.Variant(3, ua.VariantType.Int16))

    
    def draw_pic(self, color):
        sg.theme('Dark Blue 3')  # please make your windows colorful

        layout = [[sg.Text('pic the ' + color + ' cover', size=(50,10),font=('Helvetica', 20))],
            [sg.Submit(size=(10,5), font=('Helvetica', 20)), sg.Cancel(size=(10,5),font=('Helvetica', 20))]]

        window = sg.Window('smart manual station', layout)

        while True:
            event, values = window.read()
            print(event, values)
            if event is None or event == 'Cancel':
                return_val = 4
                self._pbl.deselect_all()
                break
            elif event == "Submit" and self._select_event.is_set():
                return_val = 3
                break
        # Finally
        window.close()
        self._select_event.clear()
        return return_val

    def draw_work(self, text):
        sg.theme('Dark Blue 3')  # please make your windows colorful

        layout = [[sg.Text(text, size=(50,10),font=('Helvetica', 20))],
            [sg.Submit(size=(10,5), font=('Helvetica', 20)), sg.Cancel(size=(10,5),font=('Helvetica', 20))]]

        window = sg.Window('smart manual station', layout)

        while True:
            event, values = window.read()
            print(event, values)
            if event is None or event == 'Cancel':
                return_val = 4
                self._pbl.deselect_all()
                break
            elif event == "Submit" and self._select_event.is_set():
                return_val = 3
                break
        # Finally
        window.close()
        self._select_event.clear()
        return return_val

    def operation_number_handler(self, op_number,order_url):
        op_number = int(op_number)
        if op_number == 801:
            Operation_par = self.client.get_node("ns=2;s=|var|CECC-LK.Application.AppModul.stAppControl.auiPar").get_value()
            if Operation_par == 0: #black
                return self.draw_pic("black")
            elif Operation_par == 1:
                #white
                self._pbl.select_port(port_number=1, callback=self._rack_callback)
                return self.draw_pic("white")
            elif Operation_par == 2:
                #blue
                self._pbl.select_port(port_number=6, callback=self._rack_callback)
                return self.draw_pic("blue")          
        
        elif op_number == 802:
            #blue
            self._pbl.select_port(port_number=6, callback=self._rack_callback)
            return self.draw_pic("blue")          
        
        elif op_number == 803:
            #black
            return self.draw_pic("black")

        elif op_number == 804:
            #white
            self._pbl.select_port(port_number=1, callback=self._rack_callback)
            return self.draw_pic("white")

        elif op_number == 510:
            if "FuseLeft" in order_url:
                self._pbl.select_port(port_number=3, callback=self._rack_callback)
                return self.draw_work("make sure a fuse is placed left (to the right for you)")
            elif "FuseRight" in order_url:
                self._pbl.select_port(port_number=3, callback=self._rack_callback)
                return self.draw_work("make sure a fuse is placed right (to the left for you)")
            elif "BothFuses" in order_url:
                self._pbl.select_port(port_number=3, callback=self._rack_callback)
                return self.draw_work("make sure both fuse are placed in the phone")
            elif "NoFuse" in order_url:
                self._pbl.select_port(port_number=3, callback=self._rack_callback)
                return self.draw_work("make sure no fuses are placed")
                
            elif "Blue" in order_url and "Top" in order_url: 
                self._pbl.select_port(port_number=6, callback=self._rack_callback)
                return self.draw_pic("blue")
            elif "White" in order_url and "Top" in order_url: 
                self._pbl.select_port(port_number=1, callback=self._rack_callback)
                return self.draw_pic("white")
                

        else: 
            print("{} not a valid operation".format(op_number))
            return 404



