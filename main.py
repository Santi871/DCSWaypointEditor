from configparser import ConfigParser
from src.logger import logger
from src.wp_editor import WaypointEditor
from src.gui import GUI


def main(config):
    editor = WaypointEditor(config, logger)

    gui = GUI(editor)
    gui.run()


if __name__ == "__main__":
    try:
        settings = ConfigParser()
        settings.read("settings.ini")
        main(settings)
    except Exception as e:
        logger.error("Exception occurred", exc_info=True)
        raise e

    logger.info("Finished")
