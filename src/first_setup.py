from configparser import ConfigParser
from shutil import copytree
from src.gui import first_time_setup_gui, detect_dcs_bios
from src.logger import get_logger
from pathlib import Path
import PySimpleGUI as PyGUI
import tempfile
import requests
import zipfile

DCS_BIOS_VERSION = '0.7.35'
DCS_BIOS_URL = "https://github.com/DCSFlightpanels/dcs-bios/releases/download/{}/DCS-BIOS.zip"

logger = get_logger(__name__)


def install_dcs_bios(dcs_path):
    try:
        with open(dcs_path + "Scripts\\Export.lua", "r") as f:
            filestr = f.read()
    except FileNotFoundError:
        filestr = str()

    with open(dcs_path + "Scripts\\Export.lua", "a") as f:
        if "dofile(lfs.writedir()..[[Scripts\\DCS-BIOS\\BIOS.lua]])" not in filestr:
            f.write(
                "\ndofile(lfs.writedir()..[[Scripts\\DCS-BIOS\\BIOS.lua]])\n")

    with tempfile.TemporaryDirectory() as tmp_dir:
        url = DCS_BIOS_URL.format(DCS_BIOS_VERSION)
        response = requests.get(url, stream=True)
        response.raise_for_status()

        with tempfile.TemporaryFile() as tmp_file:
            for block in response.iter_content(1024):
                tmp_file.write(block)

            with zipfile.ZipFile(tmp_file) as zip_ref:
                zip_ref.extractall(tmp_dir)

            copytree(tmp_dir + '\\DCS-BIOS', dcs_path + "Scripts\\DCS-BIOS")

            PyGUI.Popup(f'DCS-BIOS v{DCS_BIOS_VERSION} successfully downloaded and installed')


def first_time_setup():
    default_dcs_path = f"{str(Path.home())}\\Saved Games\\DCS.openbeta\\"

    setup_logger = get_logger("setup")
    setup_logger.info("Running first time setup...")

    gui = first_time_setup_gui()

    while True:
        event, values = gui.Read()
        if event is None:
            return False

        dcs_path = values.get("dcs_path")
        if dcs_path is not None and not dcs_path.endswith("\\") and not dcs_path.endswith("/"):
            dcs_path = dcs_path + "\\"

        if event == "accept_button":
            break
        elif event == "install_button":
            try:
                setup_logger.info("Installing DCS BIOS...")
                install_dcs_bios(dcs_path)
                gui.Element("install_button").Update(disabled=True)
                gui.Element("accept_button").Update(disabled=False)
                gui.Element("dcs_bios").Update(value="Installed")
            except (FileExistsError, FileNotFoundError, requests.HTTPError) as e:
                gui.Element("dcs_bios").Update(value="Failed to install")
                setup_logger.error("DCS-BIOS failed to install", exc_info=True)
                PyGUI.Popup(f"DCS-BIOS failed to install:\n{e}")
        elif event == "dcs_path":
            dcs_bios_detected = detect_dcs_bios(values["dcs_path"])
            if dcs_bios_detected:
                gui.Element("install_button").Update(disabled=True)
                gui.Element("accept_button").Update(disabled=False)
                gui.Element("dcs_bios").Update(value="Detected")
            else:
                gui.Element("install_button").Update(disabled=False)
                gui.Element("accept_button").Update(disabled=True)
                gui.Element("dcs_bios").Update(value="Not detected")

    config = ConfigParser()
    config.add_section("PREFERENCES")
    config.set("PREFERENCES", "grace_period", "5")
    config.set("PREFERENCES", "button_release_short_delay", "0.2")
    config.set("PREFERENCES", "button_release_medium_delay", "0.5")
    config.set("PREFERENCES", "tesseract_path", values.get("tesseract_path"))
    config.set("PREFERENCES", "dcs_path", dcs_path or default_dcs_path)
    config.set("PREFERENCES", "db_name", "profiles_new.db")
    config.set("PREFERENCES", "capture_key", values.get("capture_key") or "ctrl+t")
    config.set("PREFERENCES", "quick_capture_hotkey", values.get("quick_capture_hotkey") or "ctrl+shift+t")
    config.set("PREFERENCES", "enter_aircraft_hotkey", values.get("enter_aircraft_hotkey") or '')
    config.set("PREFERENCES", "log_raw_tesseract_output", "false")

    with open("settings.ini", "w+") as f:
        config.write(f)

    setup_logger.info("First time setup completed succesfully")
    gui.Close()
    return True
