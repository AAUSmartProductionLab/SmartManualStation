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
                port_number, instructions = self.operation_number_to_port(Operation_number,Order_url)
                
                if port_number:
                    self._pbl.select_port(port_number,instructions=instructions)

                    # wait until work has finished or status tag changed.
                    while self._pbl.get_port_state(port_number).work_finished == False:
                        if flag.get_value() != 2:
                            self._pbl.work_finished(port_number)
                        sleep(0.25)

                # finally set the flag to 3 to signal that we are done.    
                flag.set_value(ua.Variant(3, ua.VariantType.Int16))
        
        logger.warning("disconnected from festo module")

    def operation_number_to_port(self, op_number,order_url):
        
        """There are multiple operations the festo system can request. some are redundant but we have to 
           concider all possible options just to be safe.

        Returns:
            [int]: port number. Returns 0 if not valid

        """

        op_number = int(op_number)

        # cover color send as a seperate parameter
        if op_number == 801:
            Operation_par = self.client.get_node("ns=2;s=|var|CECC-LK.Application.AppModul.stAppControl.auiPar").get_value()
            if Operation_par == 0: 
                #black
                return 6 , "Place a black bottom cover on the pallet"
            elif Operation_par == 1:
                #white
                return 5 , "Place a white bottom cover on the pallet"
            elif Operation_par == 2:
                #blue
                return 4 , "Place a blue bottom cover on the pallet"
        
        
        elif op_number == 803:
            #black
            return 6, "Place a black bottom cover on the pallet"

        elif op_number == 804:
            #white
            return 5 , "Place a white bottom cover on the pallet"
        elif op_number == 802:
            #blue
            return 4 , "Place a blue bottom cover on the pallet"

        # repare operations and generic manual operations
        elif op_number == 510:
            if "FuseLeft" in order_url:
                return 3, "make sure a fuse is placed left (to the right for you)"
            elif "FuseRight" in order_url:
                return 3,  "make sure a fuse is placed right (to the left for you)"
            elif "BothFuses" in order_url:
                return 3,  "make sure both fuse are placed in the phone"
            elif "NoFuse" in order_url:
                return 3,  "make sure no fuses are placed"
                
            elif "Blue" in order_url and "Top" in order_url: 
                return 1, "Press the blue top cover on the phone. Make sure it is oriented correctly"
            elif "White" in order_url and "Top" in order_url: 
                return 2, "press the white top cover on the phone. Make sure it is oriented correctly"

        # if we get here nothing matched the possible operations that we know of.
        logger.warning("{} not a valid operation for this station".format(op_number))
        return 0, "Received unknown operation id. id = {}".format(op_number)



