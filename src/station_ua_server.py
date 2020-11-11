from opcua import ua, Server, Node
from time import sleep
from threading import Thread, Event
from datetime import datetime

import logging  
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

class StationUAServer:
    def __init__(self,pick_by_light):
        self._pbl = pick_by_light
        self._setup_nodes()
        self._generate_tags()

        self.ua_server.start()
        
        self._generate_subscriptions()
        Thread(target=self._var_updater, daemon=True).start()

    def _setup_nodes(self):        
        
        # Create server instance 
        self.ua_server = Server('./opcua_cache')
        self.ua_server.set_endpoint('opc.tcp://0.0.0.0:4840/UA/PickByLight')
        self.ua_server.set_server_name("Pick By Light Server")
        # idx name will be used later for creating the xml used in data type dictionary
        # setup our own namespace, not really necessary but should as spec
        idx_name = 'http://examples.freeopcua.github.io'
        self.idx = self.ua_server.register_namespace(idx_name)
        
        # Set all possible endpoint policies for clients to connect through
        self.ua_server.set_security_policy([
            ua.SecurityPolicyType.NoSecurity,
            ua.SecurityPolicyType.Basic128Rsa15_SignAndEncrypt,
            ua.SecurityPolicyType.Basic128Rsa15_Sign,
            ua.SecurityPolicyType.Basic256_SignAndEncrypt,
            ua.SecurityPolicyType.Basic256_Sign])

        # get Objects node, this is where we should put our custom stuff
        objects = self.ua_server.get_objects_node()

        # Create objects for the pack tags using the above created packMLBasedObjectType
        self.Status = objects.add_folder('ns=2;s=Status', "Status")
        self.Command = objects.add_folder('ns=2;s=Command', "Command")
        self.Command.add_method('ns=2;s=Command.SelectPort', "SelectPort", self._select_method, [ua.VariantType.Int32, ua.VariantType.String], [ua.VariantType.Boolean])
        self.Command.add_method('ns=2;s=Command.DeselectPort', "DeselectPort", self._deselect_method, [ua.VariantType.Int32], [ua.VariantType.Boolean])
        self.Command.add_method('ns=2;s=Command.DeselectAllPorts', "DeselectAllPorts", self._deselect_all_method, [], [ua.VariantType.Boolean])


        root = self.ua_server.get_root_node()
        DummyFestoObj = root.add_object("ns=2;s=|var|CECC-LK.Application.Flexstation_globalVariables", "DummyFesto")
        DummyFestoObj.add_variable("ns=2;s=|var|CECC-LK.Application.Flexstation_globalVariables.FlexStationStatus", "FlexStationStatus", val=0).set_writable()
        DummyFestoObj.add_variable("ns=2;s=|var|CECC-LK.Application.FBs.stpStopper1.stAppControl.uiOpNo","uiOpNo", val=0).set_writable()
        

    def _generate_tags(self):
        # for all ports generate tags
        for port_number, port in self._pbl.get_ports():
            # Make a folder with the port_number as the name
            b_obj = self.Status.add_object('ns=2;s=Status.Port_{}'.format(port_number), "Port_{}".format(port_number))
            
            content = self._pbl.get_content(port_number)

            b_obj.add_variable("ns=2;s=Status.Port_{}.Selected".format(port_number)             ,"Selected"            , bool())
            b_obj.add_variable("ns=2;s=Status.Port_{}.Instructions".format(port_number)         ,"Instructions"        , "")
            b_obj.add_variable("ns=2;s=Status.Port_{}.Activity".format(port_number)             ,"Activity"            , bool())
            b_obj.add_variable("ns=2;s=Status.Port_{}.ActivityTimestamp".format(port_number)    ,"ActivityTimestamp"   , datetime.fromtimestamp(0))
            b_obj.add_variable("ns=2;s=Status.Port_{}.LightState".format(port_number)           ,"LightState"          , 0)
            b_obj.add_variable("ns=2;s=Status.Port_{}.ContentDisplayName".format(port_number)   ,"ContentDisplayName"  , content['display_name'])
            b_obj.add_variable("ns=2;s=Status.Port_{}.ContentName".format(port_number)          ,"ContentName"         , content['name'])
            b_obj.add_variable("ns=2;s=Status.Port_{}.ContentDescription".format(port_number)   ,"ContentDescription"  , content['description'])
            b_obj.add_variable("ns=2;s=Status.Port_{}.ContentImagePath".format(port_number)     ,"ContentImagePath"    , content['image_path'])

            '''
            create command tags for clients that does not support ua methods. 
            '''
            b_obj = self.Command.add_object('ns=2;s=Command.Port_{}'.format(port_number), "Port_{}".format(port_number))

            b_obj.add_variable("ns=2;s=Command.Port_{}.Selected".format(port_number)             ,"Selected"            , bool()).set_writable()
            b_obj.add_variable("ns=2;s=Command.Port_{}.Instructions".format(port_number)         ,"Instructions"        , "").set_writable()
            b_obj.add_variable("ns=2;s=Command.Port_{}.ContentDisplayName".format(port_number)   ,"ContentDisplayName"  , content['display_name']).set_writable()
            b_obj.add_variable("ns=2;s=Command.Port_{}.ContentName".format(port_number)          ,"ContentName"         , content['name']).set_writable()
            b_obj.add_variable("ns=2;s=Command.Port_{}.ContentDescription".format(port_number)   ,"ContentDescription"  , content['description']).set_writable()
            b_obj.add_variable("ns=2;s=Command.Port_{}.ContentImagePath".format(port_number)     ,"ContentImagePath"    , content['image_path']).set_writable()

    def _generate_subscriptions(self):
        # Create UA subscriber node for the box. Set self as handler.
        sub = self.ua_server.create_subscription(100, self)
 
        # Subscribe to the Select tag and all the content tags
        for port_number, port in self._pbl.get_ports():
            a = self.ua_server.get_node("ns=2;s=Status.Port_{}.Selected".format(port_number))
            sub.subscribe_data_change(a)
            ac = self.ua_server.get_node("ns=2;s=Command.Port_{}.Selected".format(port_number))
            sub.subscribe_data_change(ac)
            b = self.ua_server.get_node("ns=2;s=Command.Port_{}.ContentDisplayName".format(port_number))
            sub.subscribe_data_change(b)
            c = self.ua_server.get_node("ns=2;s=Command.Port_{}.ContentName".format(port_number))
            sub.subscribe_data_change(c)
            d = self.ua_server.get_node("ns=2;s=Command.Port_{}.ContentDescription".format(port_number))
            sub.subscribe_data_change(d)
            e = self.ua_server.get_node("ns=2;s=Command.Port_{}.ContentImagePath".format(port_number))
            sub.subscribe_data_change(e)

    def _event_notification(self, event):
        logger.warning("Python: New event. No function implemented. {}".format(event))

    def _select_method(self,parrent,port_number, instructions):
        r = self._pbl.select_port(port_number.Value, instructions = instructions.Value)
        return [ua.Variant(value = r, varianttype=ua.VariantType.Boolean)]

    def _deselect_method(self,parrent,port_number):
        r = self._pbl.deselect_port(port_number.Value)
        return [ua.Variant(value = r,varianttype=ua.VariantType.Boolean)]

    def _deselect_all_method(self,parrent):
        r = self._pbl.deselect_all()
        return [ua.Variant(value = r,varianttype=ua.VariantType.Boolean)]

    def datachange_notification(self, node, val, data):
        """UA server callback on data change notifications        
        Arguments:
            node {Node} -- [description]
            val {[type]} -- [description]
            data {[type]} -- [description]
        """
        
        logger.debug("New data change event. node:{}, value:{}".format(node, val))
        
        # Sorry about these two lines of code, but I don't see any nicer way of determining the port number than from 
        # the identifier string. Then splitting it up to isolate the port number.
        # Example "Status.Port_2.Selected"  is split into ['Status', 'Port_2', 'Selected'] then 'Port_2' is split into 
        # ['Port', '2'] and then the '2' is turned into an intiger.
        name = str(node.nodeid.Identifier).split(".")
        port_number = int(name[1].split("_")[1])
        
        # Remember if this as a status tag. Special case to auto set the command tag back to false when ever the port
        # is deselected.
        isStatus = name[0] == "Status"
        
        # using the split name we can assume that the last term is the tag that updated.
        tag = name[-1] 
        
        """ Switch for each possible tag"""
        # If the status tag "selected" changes to false. Automatically set the command tag back to false as well. 
        if tag == 'Selected' and isStatus:
            if val == False:
                node = self.ua_server.get_node("ns=2;s=Command.Port_{}.Selected".format(port_number))
                node.set_value(False)

        # If the command tag "Selected" changes go select that port with the instructions saved in the command tag. 
        elif tag == 'Selected' and not isStatus:
            if val == True:
                node = self.ua_server.get_node("ns=2;s=Command.Port_{}.Instructions".format(port_number))
                instructions = node.get_value()
                self._pbl.select_port(port_number, instructions=instructions)
            else:
                self._pbl.deselect_port(port_number)

        elif tag == 'ContentDisplayName':
                self._pbl.set_content_key(port_number,'display_name', str(val))
        elif tag == 'ContentName':
                self._pbl.set_content_key(port_number,'name', str(val))
        elif tag == 'ContentDescription':
                self._pbl.set_content_key(port_number,'description', str(val))
        elif tag == 'ContentImagePath':
                self._pbl.set_content_key(port_number,'image_path', str(val))
    

    def _var_updater(self):
        while True:
            sleep(0.1)
            # for all boxes update tags
            for port_number, port in self._pbl.get_ports():
                # get the object in the packml status object using our unique idx
                node = self.ua_server.get_node("ns=2;s=Status.Port_{}.Activity".format(port_number))
                node.set_value(port.activity)          
                node = self.ua_server.get_node("ns=2;s=Status.Port_{}.ActivityTimestamp".format(port_number))
                node.set_value(port.activity_timestamp) 
                node = self.ua_server.get_node("ns=2;s=Status.Port_{}.LightState".format(port_number))
                node.set_value(port.get_light())            
            
                state = self._pbl.get_port_state(port_number)         
                node = self.ua_server.get_node("ns=2;s=Status.Port_{}.Selected".format(port_number))
                node.set_value(state.selected)
                node = self.ua_server.get_node("ns=2;s=Status.Port_{}.Instructions".format(port_number))
                node.set_value(state.select_instructions)

                content = self._pbl.get_content(port_number)
                node = self.ua_server.get_node("ns=2;s=Status.Port_{}.ContentDisplayName".format(port_number))
                node.set_value(content['display_name'])
                node = self.ua_server.get_node("ns=2;s=Status.Port_{}.ContentName".format(port_number))
                node.set_value(content['name'])
                node = self.ua_server.get_node("ns=2;s=Status.Port_{}.ContentDescription".format(port_number))
                node.set_value(content['description'])
                node = self.ua_server.get_node("ns=2;s=Status.Port_{}.ContentImagePath".format(port_number))
                node.set_value(content['image_path'])
