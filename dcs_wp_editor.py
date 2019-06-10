from configparser import ConfigParser
from src.logger import get_logger, log_settings
from src.wp_editor import WaypointEditor
from src.gui import GUI, exception_gui, check_version
from src.first_setup import first_time_setup
from src.objects import generate_default_bases
import traceback
import logging
from pyproj import datadir, _datadir


version = "v0.9.2b2"


def main():
    try:
        open("settings.ini", "r").close()
        first_time = False
    except FileNotFoundError:
        first_time = True

    update_exit = check_version(version)
    if update_exit:
        return

    setup_completed = not first_time or first_time_setup()

    if setup_completed:
        generate_default_bases()
        log_settings()
        settings = ConfigParser()
        settings.read("settings.ini")
        editor = WaypointEditor(settings)

        gui = GUI(editor, version)

        try:
            gui.run()
        except Exception:
            gui.close()
            raise


if __name__ == "__main__":
    logger = get_logger("root")
    logger.info("Initializing")

    try:
        main()
    except Exception as e:
        logger.error("Exception occurred", exc_info=True)
        logging.shutdown()
        exception_gui(traceback.format_exc())
        raise

    logger.info("Finished")
