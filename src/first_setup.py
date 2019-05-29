from configparser import ConfigParser
from shutil import copytree
from src.gui import first_time_setup_gui
from src.logger import get_logger
from pathlib import Path
import os


def install_dcs_bios(dcs_path):
    with open(dcs_path + "Scripts\\Export.lua", "r") as f:
        filestr = f.read()

    with open(dcs_path + "Scripts\\Export.lua", "a") as f:
        if "dofile(lfs.writedir()..[[Scripts\\DCS-BIOS\\BIOS.lua]])" not in filestr:
            f.write("\ndofile(lfs.writedir()..[[Scripts\\DCS-BIOS\\BIOS.lua]])\n")

    copytree(".\\DCS-BIOS", dcs_path + "Scripts\\DCS-BIOS")


def first_time_setup():
    default_dcs_path = f"{str(Path.home())}\\Saved Games\\DCS.openbeta\\"
    default_tesseract_path = f"{os.environ['PROGRAMW6432']}\\Tesseract-OCR\\tesseract.exe"

    setup_logger = get_logger("setup")
    setup_logger.info("Running first time setup...")

    gui = first_time_setup_gui()

    while True:
        event, values = gui.Read()

        if event is None:
            return False
        elif event == "Accept":
            break
        elif event == "Install":
            try:
                install_dcs_bios(values["dcs_path"])
                gui.Element("Install").Update(disabled=True)
                gui.Element("Accept").Update(disabled=False)
                gui.Element("dcs_bios").Update(value="Installed")
            except (FileExistsError, FileNotFoundError) as exc:
                gui.Close()
                raise Exception("Failed to install DCS-BIOS: " + str(exc))

    config = ConfigParser()
    config.add_section("PREFERENCES")
    config.set("PREFERENCES", "grace_period", "5")
    config.set("PREFERENCES", "tesseract_path", default_tesseract_path or values.get("tesseract_path"))
    config.set("PREFERENCES", "dcs_path", default_dcs_path or values.get("dcs_path"))
    config.set("PREFERENCES", "db_name", "profiles.db")
    config.set("PREFERENCES", "capture_key", "left ctrl+t" or values.get("capture_key"))

    with open("settings.ini", "w+") as f:
        config.write(f)

    setup_logger.info("First time setup completed succesfully")
    gui.Close()
    return True
