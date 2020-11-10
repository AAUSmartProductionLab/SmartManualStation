#!/usr/var/Python3

import argparse
import pick_by_light
import gui
import station_ua_server as suas
import coloredlogs, logging  
import os

coloredlogs.install(level = logging.WARNING)
logger = logging.getLogger(__name__)


parser = argparse.ArgumentParser(
    description='Smart Manual Station Project at Aalborg University'
)
parser.add_argument("-v", "--verbose", help="increase output verbosity", action="store_true")
parser.add_argument("-d", "--dummy", help="run in dummy mode without the actual hardware", action="store_true")
parser.add_argument("-C", "--content_map", help="path to the content map", action="store_true")


args = parser.parse_args()
if args.verbose:
    logger.setLevel(logging.DEBUG)
    pick_by_light.logger.setLevel(logging.DEBUG)
    suas.logger.setLevel(logging.DEBUG)
    gui.logger.setLevel(logging.DEBUG)

# Load either the dummy ports or the pi ports 
if args.dummy:
    from dummy_port import DummyPort as Port
    logger.warn("Running in dummy mode")
else:
    from pi_port import PiPort as Port
    # load the default ports
    Port.load_pinout_from_file(pin_conf_name = 'default_pin_config.yaml')

if args.content_map:
    content_map = args.content_map
else:
    content_map = 'content_map.yaml'


if __name__ == "__main__":
    from time import sleep
    # generate a bunch of ports 
    ports = [Port(i) for i in range(1,7)]

    # create our pick by light object
    PBL = pick_by_light.PickByLight(ports, default_content_map_path=content_map)

    PBL.select_port(1)

    SUAS = suas.StationUAServer(PBL)

    GUI = gui.Gui(PBL)


    try:
        # GUI.run blocks untill it exits
        GUI.run()
        SUAS.ua_server.stop()
    except KeyboardInterrupt:
        print('interrupted!')

