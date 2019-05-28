from configparser import ConfigParser
from src.logger import get_logger, log_settings
from src.wp_editor import WaypointEditor
from src.gui import GUI, first_time_setup_gui
from pyproj import datadir, _datadir


def first_time_setup():
    gui = first_time_setup_gui()

    while True:
        event, values = gui.Show()

        if event is None:
            return False
        elif event == "Install":

            gui.Element("Accept").Update(disabled=False)
            break

    config = ConfigParser()
    config.add_section("PREFERENCES")
    config.set("PREFERENCES", "Grace_Period", "5")
    config.set("PREFERENCES", "Tesseract_Path", values["tesseract_path"])
    config.set("PREFERENCES", "DCS_Path", values["dcs_path"])
    config.set("PREFERENCES", "DB_Name", "profiles.db")

    with open("settings.ini", "w+") as f:
        config.write(f)

    return True


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
        gui.run()


if __name__ == "__main__":
    logger = get_logger("root")
    logger.info("Initializing")

    try:
        main()
    except Exception as e:
        logger.error("Exception occurred", exc_info=True)
        raise e

    logger.info("Finished")
