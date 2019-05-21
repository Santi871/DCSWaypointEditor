from time import sleep
from configparser import ConfigParser
import sys
from src.logger import logger
from src.wp_editor import WaypointEditor


def main():
    settings = ConfigParser()
    settings.read("settings.ini")
    preferences = settings['PREFERENCES']

    try:
        editor = WaypointEditor(sys.argv[1], settings, logger)
    except IndexError:
        editor = WaypointEditor('waypoints.ini', settings, logger)

    active_wps, active_msns = editor.build_msns_and_wps()

    for i in reversed(range(preferences.getint('Grace_Period', 5))):
        logger.info(f"Entering data in {i+1}...")
        sleep(1)

    if active_wps:
        logger.info(f"Entering {len(active_wps)} waypoints")
        editor.enter_waypoints(active_wps)

    sleep(1)

    if active_msns:
        logger.info(f"Entering {len(active_msns)} PP missions")
        editor.enter_missions(active_msns)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error("Exception occurred", exc_info=True)
        raise e

    logger.info("Finished")
