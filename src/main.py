#!/usr/bin/python3

import argparse
import pick_by_light
import gui
import station_ua_server as suas
import station_festo_connect as festo_connect
import coloredlogs, logging  
import os

coloredlogs.install(level = logging.WARNING)
logger = logging.getLogger(__name__)

# Allow for arguments being passed to this file 
parser = argparse.ArgumentParser(
    description='Smart Manual Station Project at Aalborg University'
)
parser.add_argument("-v", "--verbose", help="increase output verbosity", action="store_true")
parser.add_argument("-d", "--dummy", help="run in dummy mode without the actual hardware", action="store_true")
parser.add_argument("-C", "--content_map", help="path to the content map", type=str)
parser.add_argument("-f", "--festo_connect", help="enable festo connect", action="store_true")
parser.add_argument("-i", "--festo_connect_ip", help="ip address for festo connect", type=str)

# If verbose flag set the debugger level accordingly on all improted files 
# TODO Setting the debug level seems to not work correctly.
args = parser.parse_args()
if args.verbose:
    logger.setLevel(logging.DEBUG)
    pick_by_light.logger.setLevel(logging.DEBUG)
    suas.logger.setLevel(logging.WARNING)
    gui.logger.setLevel(logging.DEBUG)

# Load either the dummy ports or the pi ports depending on passed argument
if args.dummy:
    from dummy_port import DummyPort as Port
    logger.warning("Running in dummy mode")
else:
    from pi_port import PiPort as Port
    # load the default ports
    Port.load_pinout_from_file(pin_conf_name = 'default_pin_config.yaml')

# If a path string for a content map has been passed, save it, else set default.
if args.content_map:
    content_map = args.content_map
else:
    content_map = 'content_map.yaml'


if __name__ == "__main__":
    # generate 6 ports 
    ports = [Port(i) for i in range(1,7)]

    # Create our pick by light object
    PBL = pick_by_light.PickByLight(ports, default_content_map_path=content_map)

    # Create our station ua serer, passing in our pick by light instance.
    SUAS = suas.StationUAServer(PBL)

    # Create our gui interface, passing in our pick by light instance.
    GUI = gui.Gui(PBL)

    if args.festo_connect:
        # Create festo connect object
        FC = festo_connect.FestoServer(PBL,args.festo_connect_ip)

    try:
        # GUI.run blocks untill it exits
        GUI.run()
    except KeyboardInterrupt:
        print('interrupted!')
    finally:
        # Finally stop the ua server
        SUAS.ua_server.stop()

