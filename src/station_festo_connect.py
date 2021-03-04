from time import sleep
from threading import Thread, Event
from opcua import ua, Client
import socket
from pick_by_light import PickByLight

import logging  
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class FestoServer():
    def __init__(self, pick_by_light: PickByLight, festo_ip: str, ua_port = '4840'):
        self._pbl = pick_by_light

        try:
            self.client = Client("opc.tcp://{}:{}".format(festo_ip, ua_port))
            self.client.connect()
            logger.info("Festo OPC-UA Client Connected")
            self.connected = True
        except socket.timeout:
            logger.warning("Failed to connect to OPC-UA on {}:{}".format(festo_ip,ua_port))
            self.connected = False

        logger.info("connected to festo module on opc.tcp://{}:{}".format(festo_ip,ua_port))
        self._select_event = Event()
        Thread(target=self.run, daemon=True).start()
        
    def run(self):
        while self.connected:
            sleep(0.1)
            
            # Read the flag on the festo system
            flag = self.client.get_node("ns=2;s=|var|CECC-LK.Application.Flexstation_globalVariables.FlexStationStatus") 
            # If flag is high
            if flag.get_value() == 1:
                # Answer back by setting the flag = 2
                flag.set_value(ua.Variant(2, ua.VariantType.Int16))
                
                # Get the operation number and order url.
                Operation_number = self.client.get_node("ns=2;s=|var|CECC-LK.Application.FBs.stpStopper1.stAppControl.uiOpNo").get_value() # change to order id
                Order_url = self.client.get_node("ns=2;s=|var|CECC-LK.Application.AppModul.stRcvData.sOderDes").get_value()
                
                # interpret the operation number nad order url
                name, instructions = self.operation_number_translator(Operation_number,Order_url)
                
                # try to select the content with the returned name.
                success, port_number = self._pbl.select_content(name=name, instructions=instructions)
                
                if success:
                    # wait until work has finished or status tag changed.
                    while self._pbl.get_port_state(port_number).work_finished == False:
                        if flag.get_value() != 2:
                            self._pbl.work_finished(port_number)
                        sleep(0.25)

                # finally set the flag to 3 to signal that we are done.    
                flag.set_value(ua.Variant(3, ua.VariantType.Int16))
        
        logger.warning("disconnected from festo module")

    def operation_number_translator(self, op_number,order_url):
        
        """There are multiple operations the festo system can request. some are redundant but we have to 
           concider all possible options just to be safe.

        Returns:
            [string]: name. Returns the name of the item to retreeve. Return empty string on failure to translate
            [string]: instructions. returns the instructions to display 

        """

        op_number = int(op_number)

        # cover color send as a separate parameter
        if op_number == 801:
            Operation_par = self.client.get_node("ns=2;s=|var|CECC-LK.Application.AppModul.stAppControl.auiPar").get_value()
            if Operation_par == 0: 
                return "black_bottom_cover" , "Place a black bottom cover on the pallet"
            elif Operation_par == 1:
                return "white_bottom_cover" , "Place a white bottom cover on the pallet"
            elif Operation_par == 2:
                return "blue_bottom_cover" , "Place a blue bottom cover on the pallet"
        
        
        elif op_number == 803:
            return "black_bottom_cover", "Place a black bottom cover on the pallet"
        elif op_number == 804:
            return "white_bottom_cover" , "Place a white bottom cover on the pallet"
        elif op_number == 802:
            return "blue_bottom_cover" , "Place a blue bottom cover on the pallet"

        # repare operations and generic manual operations
        elif op_number == 510:
            if "FuseLeft" in order_url:
                return "fuse_1A", "make sure a fuse is placed left (to the right for you)"
            elif "FuseRight" in order_url:
                return "fuse_1A",  "make sure a fuse is placed right (to the left for you)"
            elif "BothFuses" in order_url:
                return "fuse_1A",  "make sure both fuse are placed in the phone"
            elif "NoFuse" in order_url:
                return "fuse_1A",  "make sure no fuses are placed"
                
            elif "Blue" in order_url and "Top" in order_url: 
                return "blue_top_cover", "Press the blue top cover on the phone. Make sure it is oriented correctly"
            elif "White" in order_url and "Top" in order_url: 
                return "white_top_cover", "press the white top cover on the phone. Make sure it is oriented correctly"

        # if we get here nothing matched the possible operations that we know of.
        logger.warning("{} not a valid operation for this station".format(op_number))
        return "", ""



