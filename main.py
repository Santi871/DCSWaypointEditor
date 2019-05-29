from configparser import ConfigParser
from src.logger import get_logger, log_settings
from src.wp_editor import WaypointEditor
from src.gui import GUI, exception_gui
from src.first_setup import first_time_setup
import traceback
from pyproj import datadir, _datadir


def main():
    try:
        open("settings.ini", "r").close()
        first_time = False
    except FileNotFoundError:
        first_time = True

    setup_results = not first_time or first_time_setup()

    if setup_results:
        log_settings()
        settings = ConfigParser()
        settings.read("settings.ini")
        editor = WaypointEditor(settings)

        gui = GUI(editor)

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
        exception_gui(traceback.format_exc())
        raise

    logger.info("Finished")
