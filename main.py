from configparser import ConfigParser
from src.logger import get_logger
from src.wp_editor import WaypointEditor
from src.gui import GUI
import socket
from time import sleep, time


HOST = '127.0.0.1'  # Standard loopback interface address (localhost)
PORT = 7778        # Port to listen on (non-privileged ports are > 1023)


def main(config):
    '''
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        while True:
            s.sendto(b"UFC_1 1\n", (HOST, PORT))
            sleep(1)
            s.sendto(b"UFC_1 0\n", (HOST, PORT))
            sleep(1)
    '''

    editor = WaypointEditor(config)

    gui = GUI(editor)
    gui.run()


if __name__ == "__main__":
    logger = get_logger("root")
    logger.info("Initializing")

    try:
        settings = ConfigParser()
        settings.read("settings.ini")
        main(settings)
    except Exception as e:
        logger.error("Exception occurred", exc_info=True)
        raise e

    logger.info("Finished")
