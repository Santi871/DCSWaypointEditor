from src.objects import Profile, Waypoint, MSN
from src.logger import get_logger
from peewee import DoesNotExist
from LatLon23 import LatLon, Longitude, Latitude, string2latlon
from PIL import ImageGrab, ImageEnhance, ImageOps
from pathlib import Path
import pytesseract
import keyboard
import os
import urllib.request
import urllib.error
import webbrowser
import base64
import pyperclip
from slpp import slpp as lua
import src.pymgrs as mgrs
import PySimpleGUI as PyGUI
import zlib
from desktopmagic.screengrab_win32 import getDisplaysAsImages
import cv2
import numpy
import re
import datetime

def json_zip(j):
    j = base64.b64encode(
        zlib.compress(
            j.encode('utf-8')
        )
    ).decode('ascii')
    return j


def json_unzip(j):
    return zlib.decompress(base64.b64decode(j)).decode('utf-8')


def strike(text):
    result = '\u0336'
    for i, c in enumerate(text):
        result = result + c
        if i != len(text)-1:
            result = result + '\u0336'
    return result


def unstrike(text):
    return text.replace('\u0336', '')


def detect_dcs_bios(dcs_path):
    dcs_bios_detected = False

    try:
        with open(dcs_path + "\\Scripts\\Export.lua", "r") as f:
            if r"dofile(lfs.writedir()..[[Scripts\DCS-BIOS\BIOS.lua]])" in f.read() and \
                    os.path.exists(dcs_path + "\\Scripts\\DCS-BIOS"):
                dcs_bios_detected = True
    except FileNotFoundError:
        pass
    return dcs_bios_detected


def first_time_setup_gui():
    default_dcs_path = f"{str(Path.home())}\\Saved Games\\DCS.openbeta\\"
    default_tesseract_path = f"{os.environ['PROGRAMW6432']}\\Tesseract-OCR\\tesseract.exe"
    dcs_bios_detected = "Detected" if detect_dcs_bios(
        default_dcs_path) else "Not detected"

    layout = [
        [PyGUI.Text("DCS User Folder Path:"), PyGUI.Input(default_dcs_path, key="dcs_path", enable_events=True),
         PyGUI.Button("Browse...", button_type=PyGUI.BUTTON_TYPE_BROWSE_FOLDER, target="dcs_path")],

        [PyGUI.Text("Tesseract.exe Path:"), PyGUI.Input(default_tesseract_path, key="tesseract_path"),
         PyGUI.Button("Browse...", button_type=PyGUI.BUTTON_TYPE_BROWSE_FILE, target="tesseract_path")],

        [PyGUI.Text("F10 Map Capture Hotkey:"), PyGUI.Input(
            "ctrl+t", key="capture_key")],

        [PyGUI.Text("Quick Capture Toggle Hotkey:"), PyGUI.Input(
            "ctrl+shift+t", key="quick_capture_hotkey")],

        [PyGUI.Text("Enter into Aircraft Hotkey (Optional):"), PyGUI.Input(
            "", key="enter_aircraft_hotkey")],

        [PyGUI.Text("DCS-BIOS:"), PyGUI.Text(dcs_bios_detected, key="dcs_bios"),
         PyGUI.Button("Install", key="install_button", disabled=dcs_bios_detected == "Detected")],
    ]

    return PyGUI.Window("First time setup", [[PyGUI.Frame("Settings", layout)],
                                             [PyGUI.Button("Accept", key="accept_button", pad=((250, 1), 1),
                                                           disabled=dcs_bios_detected != "Detected")]])


def exception_gui(exc_info):
    return PyGUI.PopupOK("An exception occured and the program terminated execution:\n\n" + exc_info)


def check_version(current_version):
    version_url = "https://raw.githubusercontent.com/Santi871/DCSWaypointEditor/master/release_version.txt"
    releases_url = "https://github.com/Santi871/DCSWaypointEditor/releases"

    try:
        with urllib.request.urlopen(version_url) as response:
            if response.code == 200:
                html = response.read()
            else:
                return False
    except (urllib.error.HTTPError, urllib.error.URLError):
        return False

    new_version = html.decode("utf-8")
    if new_version != current_version:
        popup_answer = PyGUI.PopupYesNo(
            f"New version available: {new_version}\nDo you wish to update?")

        if popup_answer == "Yes":
            webbrowser.open(releases_url)
            return True
        else:
            return False


def try_get_setting(settings, setting_name, setting_fallback, section="PREFERENCES"):
    if settings.has_option(section, setting_name):
        return settings.get(section, setting_name)
    else:
        settings[section][setting_name] = setting_fallback
        with open("settings.ini", "w") as configfile:
            settings.write(configfile)
        return setting_fallback


class GUI:
    def __init__(self, editor, software_version):
        self.logger = get_logger("gui")
        self.editor = editor
        self.captured_map_coords = None
        self.profile = Profile('')
        self.profile.aircraft = "hornet"
        self.exit_quick_capture = False
        self.values = None
        self.capturing = False
        self.capture_key = try_get_setting(self.editor.settings, "capture_key", "ctrl+t")
        self.quick_capture_hotkey = try_get_setting(self.editor.settings, "quick_capture_hotkey", "ctrl+alt+t")
        self.enter_aircraft_hotkey = try_get_setting(self.editor.settings, "enter_aircraft_hotkey", "ctrl+shift+t")
        self.save_debug_images = try_get_setting(self.editor.settings, "save_debug_images", "false")
        self.software_version = software_version
        self.is_focused = True
        self.scaled_dcs_gui = False
        self.selected_wp_type = "WP"

        try:
            with open(f"{self.editor.settings.get('PREFERENCES', 'dcs_path')}\\Config\\options.lua", "r") as f:
                dcs_settings = lua.decode(f.read().replace("options = ", ""))
                self.scaled_dcs_gui = dcs_settings["graphics"]["scaleGui"]
        except (FileNotFoundError, ValueError, TypeError):
            self.logger.error("Failed to decode DCS settings", exc_info=True)

        tesseract_path = self.editor.settings['PREFERENCES'].get(
            'tesseract_path', "tesseract")
        self.logger.info(f"Tesseract path is: {tesseract_path}")
        pytesseract.pytesseract.tesseract_cmd = tesseract_path
        try:
            self.tesseract_version = pytesseract.get_tesseract_version()
            self.capture_status = "Status: Not capturing"
            self.capture_button_disabled = False
        except pytesseract.pytesseract.TesseractNotFoundError:
            self.tesseract_version = None
            self.capture_status = "Status: Tesseract not found"
            self.capture_button_disabled = True

        self.logger.info(f"Tesseract version is: {self.tesseract_version}")
        self.window = self.create_gui()
        keyboard.add_hotkey(self.quick_capture_hotkey, self.toggle_quick_capture)
        if self.enter_aircraft_hotkey != '':
            keyboard.add_hotkey(self.enter_aircraft_hotkey, self.enter_coords_to_aircraft)

    def exit_capture(self):
        self.exit_quick_capture = True

    @staticmethod
    def get_profile_names():
        return [profile.name for profile in Profile.list_all()]

    def create_gui(self):
        self.logger.debug("Creating GUI")

        latitude_col1 = [
            [PyGUI.Text("Degrees")],
            [PyGUI.InputText(size=(10, 1), key="latDeg", enable_events=True)],
        ]

        latitude_col2 = [
            [PyGUI.Text("Minutes")],
            [PyGUI.InputText(size=(10, 1), key="latMin", enable_events=True)],
        ]

        latitude_col3 = [
            [PyGUI.Text("Seconds")],
            [PyGUI.InputText(size=(10, 1), key="latSec",
                             pad=(5, (3, 10)), enable_events=True)],
        ]

        longitude_col1 = [
            [PyGUI.Text("Degrees")],
            [PyGUI.InputText(size=(10, 1), key="lonDeg", enable_events=True)],
        ]

        longitude_col2 = [
            [PyGUI.Text("Minutes")],
            [PyGUI.InputText(size=(10, 1), key="lonMin", enable_events=True)],
        ]

        longitude_col3 = [
            [PyGUI.Text("Seconds")],
            [PyGUI.InputText(size=(10, 1), key="lonSec",
                             pad=(5, (3, 10)), enable_events=True)],
        ]

        frameelevationlayout = [
            [PyGUI.Text("Feet")],
            [PyGUI.InputText(size=(20, 1), key="elevFeet",
                             enable_events=True)],
            [PyGUI.Text("Meters")],
            [PyGUI.InputText(size=(20, 1), key="elevMeters",
                             enable_events=True, pad=(5, (3, 10)))],
        ]

        mgrslayout = [
            [PyGUI.InputText(size=(20, 1), key="mgrs",
                             enable_events=True, pad=(5, (3, 12)))],
        ]

        framedatalayoutcol2 = [
            [PyGUI.Text("Name")],
            [PyGUI.InputText(size=(20, 1), key="msnName", pad=(5, (3, 10)))],
        ]

        framewptypelayout = [
            [PyGUI.Radio("WP", group_id="wp_type", default=True, enable_events=True, key="WP"),
             PyGUI.Radio("MSN", group_id="wp_type",
                         enable_events=True, key="MSN"),
             PyGUI.Radio("FP", group_id="wp_type", key="FP", enable_events=True),
             PyGUI.Radio("ST", group_id="wp_type", key="ST", enable_events=True)],
            [PyGUI.Radio("IP", group_id="wp_type", key="IP", enable_events=True),
             PyGUI.Radio("DP", group_id="wp_type", key="DP", enable_events=True),
             PyGUI.Radio("HA", group_id="wp_type", key="HA", enable_events=True),
             PyGUI.Radio("HB", group_id="wp_type", key="HB", enable_events=True)],
            [PyGUI.Button("Quick Capture", disabled=self.capture_button_disabled, key="quick_capture", pad=(5, (3, 8))),
             PyGUI.Text("Sequence:", pad=((0, 1), 3),
                        key="sequence_text", auto_size_text=False, size=(8, 1)),
             PyGUI.Combo(values=("None", 1, 2, 3), default_value="None",
                         auto_size_text=False, size=(5, 1), readonly=True,
                         key="sequence", enable_events=True)]
        ]

        frameactypelayout = [
            [
                PyGUI.Radio("F/A-18C", group_id="ac_type",
                            default=True, key="hornet", enable_events=True),
                PyGUI.Radio("AV-8B", group_id="ac_type",
                            disabled=False, key="harrier", enable_events=True),
                PyGUI.Radio("M-2000C", group_id="ac_type",
                            disabled=False, key="mirage", enable_events=True),
                PyGUI.Radio("F-14A/B", group_id="ac_type",
                            disabled=False, key="tomcat", enable_events=True),
                PyGUI.Radio("A-10C", group_id="ac_type",
                            disabled=False, key="warthog", enable_events=True),
            ],
            [PyGUI.Radio("F-16C", group_id="ac_type", disabled=False, key="viper", enable_events=True),]
        ]

        framelongitude = PyGUI.Frame("Longitude", [[PyGUI.Column(longitude_col1), PyGUI.Column(longitude_col2),
                                                    PyGUI.Column(longitude_col3)]])
        framelatitude = PyGUI.Frame("Latitude", [[PyGUI.Column(latitude_col1), PyGUI.Column(latitude_col2),
                                                  PyGUI.Column(latitude_col3)]])
        frameelevation = PyGUI.Frame(
            "Elevation", frameelevationlayout, pad=(5, (3, 10)))
        frameactype = PyGUI.Frame("Aircraft Type", frameactypelayout)

        framepositionlayout = [
            [framelatitude],
            [framelongitude],
            [frameelevation,
             PyGUI.Column(
                 [
                     [PyGUI.Frame("MGRS", mgrslayout)],
                     [PyGUI.Button("Capture from DCS F10 map", disabled=self.capture_button_disabled, key="capture",
                                   pad=(1, (18, 3)))],

                     [PyGUI.Text(self.capture_status, key="capture_status",
                                 auto_size_text=False, size=(20, 1))],
                 ]
             )
             ],

        ]

        frameposition = PyGUI.Frame("Position", framepositionlayout)
        framedata = PyGUI.Frame("Data", framedatalayoutcol2)
        framewptype = PyGUI.Frame("Waypoint Type", framewptypelayout)

        col0 = [
            [PyGUI.Text("Select profile:")],
            [PyGUI.Combo(values=[""] + self.get_profile_names(), readonly=True,
                         enable_events=True, key='profileSelector', size=(27, 1))],
            [PyGUI.Listbox(values=list(), size=(30, 27),
                           enable_events=True, key='activesList')],
            [PyGUI.Button("Add", size=(12, 1)),
             PyGUI.Button("Update", size=(12, 1))],
            [PyGUI.Button("Remove", size=(26, 1))],
            # [PyGUI.Button("Move up", size=(12, 1)),
            # PyGUI.Button("Move down", size=(12, 1))],
            [PyGUI.Button("Save profile", size=(12, 1)),
             PyGUI.Button("Delete profile", size=(12, 1))],
            [PyGUI.Text(f"Version: {self.software_version}")]
        ]

        col1 = [
            [PyGUI.Text("Select preset location")],
            [PyGUI.Combo(values=[""] + sorted([base.name for _, base in self.editor.default_bases.items()],),
                         readonly=False, enable_events=True, key='baseSelector'),
             PyGUI.Button(button_text="F", key="filter")],
            [framedata, framewptype],
            [frameposition],
            [frameactype],
            [PyGUI.Button("Enter into aircraft", key="enter")],
        ]

        colmain1 = [
            [PyGUI.MenuBar([["Profile",
                             [[
                                 ["Import", ["Paste as string from clipboard", "Load from encoded file", "Import from CombatFlite NS430 data"]]],
                                 "Export", ["Copy as string to clipboard", "Copy plain text to clipboard",
                                            "Save as encoded file"],
                              ]]])],
            [PyGUI.Column(col1)],
        ]

        layout = [
            [PyGUI.Column(col0), PyGUI.Column(colmain1)],
        ]

        return PyGUI.Window('DCS Waypoint Editor', layout)

    def set_sequence_station_selector(self, mode):
        if mode is None:
            self.window.Element("sequence_text").Update(value="Sequence:")
            self.window.Element("sequence").Update(
                values=("None", 1, 2, 3), value="None", disabled=True)
        if mode == "sequence":
            self.window.Element("sequence_text").Update(value="Sequence:")
            self.window.Element("sequence").Update(
                values=("None", 1, 2, 3), value="None", disabled=False)
        elif mode == "station":
            self.window.Element("sequence_text").Update(value="    Station:")
            self.window.Element("sequence").Update(
                values=(8, 7, 3, 2), value=8, disabled=False)

    def update_position(self, position=None, elevation=None, name=None, update_mgrs=True, aircraft=None,
                        waypoint_type=None):

        if position is not None:
            latdeg = round(position.lat.degree)
            latmin = round(position.lat.minute)
            latsec = round(position.lat.second, 2)

            londeg = round(position.lon.degree)
            lonmin = round(position.lon.minute)
            lonsec = round(position.lon.second, 2)
            mgrs_str = mgrs.encode(mgrs.LLtoUTM(
                position.lat.decimal_degree, position.lon.decimal_degree), 5)
        else:
            latdeg = ""
            latmin = ""
            latsec = ""

            londeg = ""
            lonmin = ""
            lonsec = ""
            mgrs_str = ""

        self.window.Element("latDeg").Update(latdeg)
        self.window.Element("latMin").Update(latmin)
        self.window.Element("latSec").Update(latsec)

        self.window.Element("lonDeg").Update(londeg)
        self.window.Element("lonMin").Update(lonmin)
        self.window.Element("lonSec").Update(lonsec)

        if elevation is not None:
            elevation = round(elevation)
        else:
            elevation = ""

        self.window.Element("elevFeet").Update(elevation)
        self.window.Element("elevMeters").Update(
            round(elevation/3.281) if type(elevation) == int else "")
        if aircraft is not None:
            self.window.Element(aircraft).Update(value=True)

        if update_mgrs:
            self.window.Element("mgrs").Update(mgrs_str)
        self.window.Refresh()

        if type(name) == str:
            self.window.Element("msnName").Update(name)
        else:
            self.window.Element("msnName").Update("")

        if waypoint_type is not None:
            self.select_wp_type(waypoint_type)

    def update_waypoints_list(self, set_to_first=False):
        values = list()
        self.profile.update_waypoint_numbers()

        for wp in sorted(self.profile.waypoints,
                         key=lambda waypoint: waypoint.wp_type if waypoint.wp_type != "MSN" else str(waypoint.station)):
            namestr = str(wp)

            if not self.editor.driver.validate_waypoint(wp):
                namestr = strike(namestr)

            values.append(namestr)

        if set_to_first:
            self.window.Element('activesList').Update(values=values, set_to_index=0)
        else:
            self.window.Element('activesList').Update(values=values)
        self.window.Element(self.profile.aircraft).Update(value=True)

    def disable_coords_input(self):
        for element_name in\
                ("latDeg", "latMin", "latSec", "lonDeg", "lonMin", "lonSec", "mgrs", "elevFeet", "elevMeters"):
            self.window.Element(element_name).Update(disabled=True)

    def enable_coords_input(self):
        for element_name in\
                ("latDeg", "latMin", "latSec", "lonDeg", "lonMin", "lonSec", "mgrs", "elevFeet", "elevMeters"):
            self.window.Element(element_name).Update(disabled=False)

    def filter_preset_waypoints_dropdown(self):
        text = self.values["baseSelector"]
        self.window.Element("baseSelector").\
            Update(values=[""] + [base.name for _, base in self.editor.default_bases.items() if
                                  text.lower() in base.name.lower()],
                   set_to_index=0)

    def add_waypoint(self, position, elevation, name=None):
        if name is None:
            name = str()

        try:
            if self.selected_wp_type == "MSN":
                station = int(self.values.get("sequence", 0))
                number = len(self.profile.stations_dict.get(station, list()))+1
                wp = MSN(position=position, elevation=int(elevation) or 0, name=name,
                         station=station, number=number)

            else:
                sequence = self.values["sequence"]
                if sequence == "None":
                    sequence = 0
                else:
                    sequence = int(sequence)

                if sequence and len(self.profile.get_sequence(sequence)) >= 15:
                    return False

                wp = Waypoint(position, elevation=int(elevation or 0),
                              name=name, sequence=sequence, wp_type=self.selected_wp_type,
                              number=len(self.profile.waypoints_of_type(self.selected_wp_type))+1)

                if sequence not in self.profile.sequences:
                    self.profile.sequences.append(sequence)

            self.profile.waypoints.append(wp)
            self.update_waypoints_list()
        except ValueError:
            PyGUI.Popup("Error: missing data or invalid data format")

        return True

    def capture_map_coords(self, x_start=101, x_width=269, y_start=5, y_height=27):
        self.logger.debug("Attempting to capture map coords")
        gui_mult = 2 if self.scaled_dcs_gui else 1

        dt = datetime.datetime.now()
        debug_dirname = dt.strftime("%Y-%m-%d-%H-%M-%S")

        if self.save_debug_images == "true":
            os.mkdir(debug_dirname)

        map_image = cv2.imread("map.bin")
        arrow_image = cv2.imread("arrow.bin")

        for display_number, image in enumerate(getDisplaysAsImages(), 1):
            self.logger.debug("Looking for map on screen " + str(display_number))

            if self.save_debug_images == "true":
                image.save(debug_dirname + "/screenshot-"+str(display_number)+".png")

            screen_image = cv2.cvtColor(numpy.array(image), cv2.COLOR_RGB2BGR)  # convert it to OpenCV format

            search_result = cv2.matchTemplate(screen_image, map_image, cv2.TM_CCOEFF_NORMED)  # search for the "MAP" text in the screenshot
            # matchTemplate returns a new greyscale image where the brightness of each pixel corresponds to how good a match there was at that point
            # so now we search for the 'whitest' pixel
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(search_result)
            self.logger.debug("Minval: " + str(min_val) + " Maxval: " + str(max_val) + " Minloc: " + str(min_loc) + " Maxloc: " + str(max_loc))
            start_x = max_loc[0] + map_image.shape[0]
            start_y = max_loc[1]

            if max_val > 0.9:  # better than a 90% match means we are on to something

                search_result = cv2.matchTemplate(screen_image, arrow_image, cv2.TM_CCOEFF_NORMED)  # now we search for the arrow icon
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(search_result)
                self.logger.debug("Minval: " + str(min_val) + " Maxval: " + str(max_val) + " Minloc: " + str(min_loc) + " Maxloc: " + str(max_loc))

                end_x = max_loc[0]
                end_y = max_loc[1] + map_image.shape[1]

                self.logger.debug("Capturing " + str(start_x) + "x" + str(start_y) + " to " + str(end_x) + "x" + str(end_y) )

                lat_lon_image = image.crop([start_x, start_y, end_x, end_y])

                if self.save_debug_images == "true":
                    lat_lon_image.save(debug_dirname + "/lat_lon_image.png")

                enhancer = ImageEnhance.Contrast(lat_lon_image)
                enhanced = enhancer.enhance(6)
                if self.save_debug_images == "true":
                    enhanced.save(debug_dirname + "/lat_lon_image_enhanced.png")

                inverted = ImageOps.invert(enhanced)
                if self.save_debug_images == "true":
                    inverted.save(debug_dirname + "/lat_lon_image_inverted.png")

                captured_map_coords = pytesseract.image_to_string(inverted)

                self.logger.debug("Raw captured text: " + captured_map_coords)
                return captured_map_coords

        self.logger.debug("Raise exception (could not find the map anywhere i guess)")

        raise ValueError("F10 map not found")

    def export_to_string(self):
        dump = str(self.profile)
        encoded = json_zip(dump)
        pyperclip.copy(encoded)
        PyGUI.Popup('Encoded string copied to clipboard, paste away!')

    def import_from_string(self):
        # Load the encoded string from the clipboard
        encoded = pyperclip.paste()
        try:
            decoded = json_unzip(encoded)
            self.profile = Profile.from_string(decoded)
            self.profile.profilename = ""
            self.logger.debug(self.profile.to_dict())
            self.editor.set_driver(self.profile.aircraft)
            self.update_waypoints_list(set_to_first=True)
            self.window.Element("profileSelector").Update(set_to_index=0)
            PyGUI.Popup('Loaded waypoint data from encoded string successfully')
        except Exception as e:
            self.logger.error(e, exc_info=True)
            PyGUI.Popup('Failed to parse profile from string')

    def load_new_profile(self):
        self.profile = Profile('')

    def parse_map_coords_string(self, coords_string, tomcat_mode=False):
        coords_string = coords_string.upper()
        # "X-00199287 Z+00523070, 0 ft"   Not sure how to convert this yet

        # "37 T FJ 36255 11628, 5300 ft"  Tessaract did not like this one because the DCS font J looks too much like )
        res = re.match("^(\d+ [a-zA-Z] [a-zA-Z][a-zA-Z] \d+ \d+), (\d+) (FT|M)$", coords_string)
        if res is not None:
            mgrs_string = res.group(1).replace(" ", "")
            decoded_mgrs = mgrs.UTMtoLL(mgrs.decode(mgrs_string))
            position = LatLon(Latitude(degree=decoded_mgrs["lat"]), Longitude(
                degree=decoded_mgrs["lon"]))
            elevation = float(res.group(2))

            if res.group(3) == "M":
                elevation = elevation * 3.281

            return position, elevation

        # "N43°10.244 E40°40.204, 477 ft"  Degrees and decimal minutes
        res = re.match("^([NS])(\d+)°([^\s]+) ([EW])(\d+)°([^,]+), (\d+) (FT|M)$", coords_string)
        if res is not None:
            lat_str = res.group(2) + " " + res.group(3) + " " + res.group(1)
            lon_str = res.group(5) + " " + res.group(6) + " " + res.group(4)
            position = string2latlon(lat_str, lon_str, "d% %M% %H")
            elevation = float(res.group(7))

            if res.group(8) == "M":
                elevation = elevation * 3.281

            return position, elevation

        # "N42-43-17.55 E40-38-21.69, 0 ft" Degrees, minutes and decimal seconds
        res = re.match("^([NS])(\d+)-(\d+)-([^\s]+) ([EW])(\d+)-(\d+)-([^,]+), (\d+) (FT|M)$", coords_string)
        if res is not None:
            lat_str = res.group(2) + " " + res.group(3) + " " + res.group(4) + " " + res.group(1)
            lon_str = res.group(6) + " " + res.group(7) + " " + res.group(8) + " " + res.group(5)
            position = string2latlon(lat_str, lon_str, "d% %m% %S% %H")
            elevation = float(res.group(9))

            if res.group(10) == "M":
                elevation = elevation * 3.281

            return position, elevation

        # "43°34'37"N 29°11'18"E, 0 ft" Degrees minutes and seconds
        res = re.match("^(\d+)°(\d+)'([^\"]+)\"([NS]) (\d+)°(\d+)'([^\"]+)\"([EW]), (\d+) (FT|M)$", coords_string)
        if res is not None:
            lat_str = res.group(1) + " " + res.group(2) + " " + res.group(3) + " " + res.group(4)
            lon_str = res.group(5) + " " + res.group(6) + " " + res.group(7) + " " + res.group(8)
            position = string2latlon(lat_str, lon_str, "d% %m% %S% %H")
            elevation = float(res.group(9))

            if res.group(10) == "M":
                elevation = elevation * 3.281

            return position, elevation

        split_string = coords_string.split(',')

        if tomcat_mode:
            latlon_string = coords_string.replace("\\", "").replace("F", "")
            split_string = latlon_string.split(' ')
            lat_string = split_string[1]
            lon_string = split_string[3]
            position = string2latlon(
                lat_string, lon_string, format_str="d%°%m%'%S")

        if not tomcat_mode:
            elevation = split_string[1].replace(' ', '')
            if "ft" in elevation:
                elevation = int(elevation.replace("ft", ""))
            elif "m" in elevation:
                elevation = round(int(elevation.replace("m", ""))*3.281)
            else:
                raise ValueError("Unable to parse elevation: " + elevation)
        else:
            elevation = self.capture_map_coords(2074, 97, 966, 32)

        self.captured_map_coords = str()
        self.logger.info("Parsed captured text: " + str(position))
        return position, elevation

    def input_parsed_coords(self):
        try:
            captured_coords = self.capture_map_coords()
            position, elevation = self.parse_map_coords_string(captured_coords)
            self.update_position(position, elevation, update_mgrs=True)
            self.update_altitude_elements("meters")
            self.window.Element('capture_status').Update("Status: Captured")
            self.logger.debug(
                "Parsed text as coords succesfully: " + str(position))
        except (IndexError, ValueError, TypeError):
            self.logger.error("Failed to parse captured text", exc_info=True)
            self.window.Element('capture_status').Update(
                "Status: Failed to capture")
        finally:
            self.enable_coords_input()
            self.window.Element('quick_capture').Update(disabled=False)
            self.window.Element('capture').Update(
                text="Capture from DCS F10 map")
            self.capturing = False

        keyboard.remove_hotkey(self.capture_key)

    def add_wp_parsed_coords(self):
        try:
            captured_coords = self.capture_map_coords()
            position, elevation = self.parse_map_coords_string(captured_coords)
        except (IndexError, ValueError, TypeError):
            self.logger.error("Failed to parse captured text", exc_info=True)
            return
        added = self.add_waypoint(position, elevation)
        if not added:
            self.stop_quick_capture()

    def toggle_quick_capture(self):
        if self.capturing:
            self.stop_quick_capture()
        else:
            self.start_quick_capture()

    def start_quick_capture(self):
        self.disable_coords_input()
        self.window.Element('capture').Update(
            text="Stop capturing")
        self.window.Element('quick_capture').Update(disabled=True)
        self.window.Element('capture_status').Update("Status: Capturing...")
        self.window.Refresh()
        keyboard.add_hotkey(
            self.capture_key,
            self.input_parsed_coords, 
            timeout=1
        )
        self.capturing = True

    def input_tomcat_alignment(self):
        try:
            captured_coords = self.capture_map_coords(2075, 343, 913, 40)
            position, elevation = self.parse_map_coords_string(captured_coords, tomcat_mode=True)
        except (IndexError, ValueError, TypeError):
            self.logger.error("Failed to parse captured text", exc_info=True)
            return

    def stop_quick_capture(self):
        try:
            keyboard.remove_hotkey(self.capture_key)
        except KeyError:
            pass

        self.enable_coords_input()
        self.window.Element('capture').Update(text="Capture from DCS F10 map")
        self.window.Element('quick_capture').Update(disabled=False)
        self.window.Element('capture_status').Update("Status: Not capturing")
        self.capturing = False

    def update_altitude_elements(self, elevation_unit):
        if elevation_unit == "feet":
            elevation = self.window.Element("elevMeters").Get()
            try:
                if elevation:
                    self.window.Element("elevFeet").Update(
                        round(int(elevation)*3.281))
                else:
                    self.window.Element("elevFeet").Update("")
            except ValueError:
                pass
        elif elevation_unit == "meters":
            elevation = self.window.Element("elevFeet").Get()
            try:
                if elevation:
                    self.window.Element("elevMeters").Update(
                        round(int(elevation)/3.281))
                else:
                    self.window.Element("elevMeters").Update("")
            except ValueError:
                pass

    def validate_coords(self):
        lat_deg = self.window.Element("latDeg").Get()
        lat_min = self.window.Element("latMin").Get()
        lat_sec = self.window.Element("latSec").Get()

        lon_deg = self.window.Element("lonDeg").Get()
        lon_min = self.window.Element("lonMin").Get()
        lon_sec = self.window.Element("lonSec").Get()

        try:
            position = LatLon(Latitude(degree=lat_deg, minute=lat_min, second=lat_sec),
                              Longitude(degree=lon_deg, minute=lon_min, second=lon_sec))

            elevation = int(self.window.Element("elevFeet").Get())
            name = self.window.Element("msnName").Get()
            return position, elevation, name
        except ValueError as e:
            self.logger.error(f"Failed to validate coords: {e}")
            return None, None, None

    def update_profiles_list(self, name):
        profiles = self.get_profile_names()
        self.window.Element("profileSelector").Update(values=[""] + profiles,
                                                      set_to_index=profiles.index(name) + 1)

    def select_wp_type(self, wp_type):
        self.selected_wp_type = wp_type

        if wp_type == "WP":
            self.set_sequence_station_selector("sequence")
        elif wp_type == "MSN":
            self.set_sequence_station_selector("station")
        else:
            self.set_sequence_station_selector(None)

        self.window.Element(wp_type).Update(value=True)

    def find_selected_waypoint(self):
        valuestr = unstrike(self.values['activesList'][0])
        for wp in self.profile.waypoints:
            if str(wp) == valuestr:
                return wp

    def remove_selected_waypoint(self):
        valuestr = unstrike(self.values['activesList'][0])
        for wp in self.profile.waypoints:
            if str(wp) == valuestr:
                self.profile.waypoints.remove(wp)

    def enter_coords_to_aircraft(self):
        self.window.Element('enter').Update(disabled=True)
        self.editor.enter_all(self.profile)
        self.window.Element('enter').Update(disabled=False)

    def run(self):
        while True:
            event, self.values = self.window.Read()
            self.logger.debug(f"Event: {event}")
            self.logger.debug(f"Values: {self.values}")

            if event is None or event == 'Exit':
                self.logger.info("Exiting...")
                break

            elif event == "Add":
                position, elevation, name = self.validate_coords()
                if position is not None:
                    self.add_waypoint(position, elevation, name)

            elif event == "Copy as string to clipboard":
                self.export_to_string()

            elif event == "Paste as string from clipboard":
                self.import_from_string()

            elif event == "Update":
                if self.values['activesList']:
                    waypoint = self.find_selected_waypoint()
                    position, elevation, name = self.validate_coords()
                    if position is not None:
                        waypoint.position = position
                        waypoint.elevation = elevation
                        waypoint.name = name
                        self.update_waypoints_list()

            elif event == "Remove":
                if self.values['activesList']:
                    self.remove_selected_waypoint()
                    self.update_waypoints_list()

            elif event == "activesList":
                if self.values['activesList']:
                    waypoint = self.find_selected_waypoint()
                    self.update_position(
                        waypoint.position, waypoint.elevation, waypoint.name, waypoint_type=waypoint.wp_type)

            elif event == "Save profile":
                if self.profile.waypoints:
                    name = self.profile.profilename
                    if not name:
                        name = PyGUI.PopupGetText(
                            "Enter profile name", "Saving profile")

                    if not name:
                        continue

                    self.profile.save(name)
                    self.update_profiles_list(name)

            elif event == "Delete profile":
                if not self.profile.profilename:
                    continue

                Profile.delete(self.profile.profilename)
                profiles = self.get_profile_names()
                self.window.Element("profileSelector").Update(
                    values=[""] + profiles)
                self.load_new_profile()
                self.update_waypoints_list()
                self.update_position()

            elif event == "profileSelector":
                try:
                    profile_name = self.values['profileSelector']
                    if profile_name != '':
                        self.profile = Profile.load(profile_name)
                    else:
                        self.profile = Profile('')
                    self.editor.set_driver(self.profile.aircraft)
                    self.update_waypoints_list()

                except DoesNotExist:
                    PyGUI.Popup("Profile not found")

            elif event == "Save as encoded file":
                filename = PyGUI.PopupGetFile("Enter file name", "Exporting profile", default_extension=".json",
                                              save_as=True, file_types=(("JSON File", "*.json"),))

                if filename is None:
                    continue

                with open(filename + ".json", "w+") as f:
                    f.write(str(self.profile))

            elif event == "Copy plain text to clipboard":
                profile_string = self.profile.to_readable_string()
                pyperclip.copy(profile_string)
                PyGUI.Popup("Profile copied as plain text to clipboard")

            elif event == "Import from CombatFlite NS430 data":
                filename = PyGUI.PopupGetFile(
                    "Enter file name", "Importing profile")

                if filename is None:
                    continue

                with open(filename, "r") as f:
                    # Need to add a step here to convert the NS430 into json, OR
                    # come up with and alternate from_string function?
                    self.profile = Profile.from_NS430(f.read())
                # self.update_waypoints_list()

                # if self.profile.profilename:
                #     self.update_profiles_list(self.profile.profilename)

            elif event == "Load from encoded file":
                filename = PyGUI.PopupGetFile(
                    "Enter file name", "Importing profile")

                if filename is None:
                    continue

                with open(filename, "r") as f:
                    self.profile = Profile.from_string(f.read())
                self.update_waypoints_list()

                if self.profile.profilename:
                    self.update_profiles_list(self.profile.profilename)

            elif event == "capture":
                if not self.capturing:
                    self.start_quick_capture()
                else:
                    self.stop_quick_capture()

            elif event == "quick_capture":
                self.exit_quick_capture = False
                self.disable_coords_input()
                self.window.Element('capture').Update(text="Stop capturing")
                self.window.Element('quick_capture').Update(disabled=True)
                self.window.Element('capture_status').Update(
                    "Status: Capturing...")
                self.capturing = True
                self.window.Refresh()
                keyboard.add_hotkey(
                    self.capture_key, self.add_wp_parsed_coords, timeout=1)

            elif event == "baseSelector":
                base = self.editor.default_bases.get(
                    self.values['baseSelector'])

                if base is not None:
                    self.update_position(
                        base.position, base.elevation, base.name)

            elif event == "enter":
                self.enter_coords_to_aircraft()

            elif event in ("MSN", "WP", "HA", "FP", "ST", "DP", "IP", "HB"):
                self.select_wp_type(event)

            elif event == "elevFeet":
                self.update_altitude_elements("meters")

            elif event == "elevMeters":
                self.update_altitude_elements("feet")

            elif event in ("latDeg", "latMin", "latSec", "lonDeg", "lonMin", "lonSec"):
                position, _, _ = self.validate_coords()

                if position is not None:
                    m = mgrs.encode(mgrs.LLtoUTM(
                        position.lat.decimal_degree, position.lon.decimal_degree), 5)
                    self.window.Element("mgrs").Update(m)

            elif event == "mgrs":
                mgrs_string = self.window.Element("mgrs").Get()
                if mgrs_string:
                    try:
                        decoded_mgrs = mgrs.UTMtoLL(mgrs.decode(mgrs_string.replace(" ", "")))
                        position = LatLon(Latitude(degree=decoded_mgrs["lat"]), Longitude(
                            degree=decoded_mgrs["lon"]))
                        self.update_position(position, update_mgrs=False)
                    except (TypeError, ValueError, UnboundLocalError) as e:
                        self.logger.error(f"Failed to decode MGRS: {e}")

            elif event in ("hornet", "tomcat", "harrier", "warthog", "mirage", "viper"):
                self.profile.aircraft = event
                self.editor.set_driver(event)
                self.update_waypoints_list()

            elif event == "filter":
                self.filter_preset_waypoints_dropdown()

        self.close()

    def close(self):
        try:
            keyboard.remove_hotkey(self.capture_key)
        except KeyError:
            pass

        self.window.Close()
        self.editor.stop()
