import argparse
import coloredlogs, logging
from pick_by_light import PickByLight


parser = argparse.ArgumentParser(
    description='Smart Manual Station Project at Aalborg University'
)
parser.add_argument("-v", "--verbose", help="increase output verbosity", action="store_true")
parser.add_argument("-d", "--dummy", help="run in dummy mode without the actual hardware", action="store_true")


args = parser.parse_args()
if args.verbose:
    coloredlogs.install(level = logging.DEBUG)
else:
    coloredlogs.install(level = logging.WARNING)

# Load either the dummy ports or the pi ports 
if args.dummy:
    from dummy_port import DummyPort as Port
    logging.warn("Running in dummy mode")
else:
    from pi_port import PiPort as Port
    # load the default ports
    Port.load_pinout_from_file(pin_conf_name = 'default_pin_config.yaml')



if __name__ == "__main__":
    from time import sleep
    # generate a bunch of ports 
    ports = [Port(i) for i in range(1,7)]

    # create our pick by light object
    PBL = PickByLight(ports)

    PBL.select_port(1)

    try:
        while True:
            PBL.get_port_state(1)
            sleep(1)
    except KeyboardInterrupt:
        print('interrupted!')

