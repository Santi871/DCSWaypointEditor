from src.objects import Wp
from src.logger import get_logger
import src.pymgrs as mgrs
import PySimpleGUI as PyGUI
from peewee import DoesNotExist
from LatLon23 import LatLon, Longitude, Latitude, string2latlon
import json
from PIL import ImageGrab, ImageEnhance, ImageOps
import pytesseract
import keyboard
from pathlib import Path
import os
import urllib.request
import urllib.error
import webbrowser
import re


def strike(text):
    result = '\u0336'
    for i, c in enumerate(text):
        result = result + c
        if i != len(text)-1:
            result = result + '\u0336'
    return result


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
    dcs_bios_detected = "Detected" if detect_dcs_bios(default_dcs_path) else "Not detected"

    layout = [
        [PyGUI.Text("DCS User Folder Path:"), PyGUI.Input(default_dcs_path, key="dcs_path", enable_events=True),
         PyGUI.Button("Browse...", button_type=PyGUI.BUTTON_TYPE_BROWSE_FOLDER, target="dcs_path")],

        [PyGUI.Text("Tesseract.exe Path:"), PyGUI.Input(default_tesseract_path, key="tesseract_path"),
         PyGUI.Button("Browse...", button_type=PyGUI.BUTTON_TYPE_BROWSE_FILE, target="tesseract_path")],

        [PyGUI.Text("F10 Map Capture Key:"), PyGUI.Input("ctrl+t", key="capture_key")],

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
        popup_answer = PyGUI.PopupYesNo(f"New version available: {new_version}\nDo you wish to update?")

        if popup_answer == "Yes":
            webbrowser.open(releases_url)
            return True
        else:
            return False


class GUI:
    def __init__(self, editor, software_version):
        self.logger = get_logger("gui")
        self.editor = editor
        self.captured_map_coords = None
        self.profile = self.editor.get_profile('')
        self.profile.aircraft = "hornet"
        self.exit_quick_capture = False
        self.values = None
        self.capturing = False
        self.capture_key = self.editor.settings.get("PREFERENCES", "capture_key")
        self.software_version = software_version

        tesseract_path = self.editor.settings['PREFERENCES'].get('tesseract_path', "tesseract")
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

    def exit_capture(self):
        self.exit_quick_capture = True

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
            [PyGUI.InputText(size=(10, 1), key="latSec", pad=(5, (3, 10)), enable_events=True)],
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
            [PyGUI.InputText(size=(10, 1), key="lonSec", pad=(5, (3, 10)), enable_events=True)],
        ]

        frameelevationlayout = [
            [PyGUI.Text("Feet")],
            [PyGUI.InputText(size=(20, 1), key="elevFeet", enable_events=True)],
            [PyGUI.Text("Meters")],
            [PyGUI.InputText(size=(20, 1), key="elevMeters", enable_events=True, pad=(5, (3, 10)))],
        ]

        mgrslayout = [
            [PyGUI.InputText(size=(20, 1), key="mgrs", enable_events=True, pad=(5, (3, 12)))],
        ]

        framedatalayoutcol2 = [
            [PyGUI.Text("Name")],
            [PyGUI.InputText(size=(20, 1), key="msnName", pad=(5, (3, 10)))],
        ]

        framewptypelayout = [
            [PyGUI.Radio("WP", group_id="wp_type", default=True, enable_events=True, key="WP"),
             PyGUI.Radio("MSN", group_id="wp_type", enable_events=True, key="MSN"),
             PyGUI.Radio("FP", group_id="wp_type", disabled=True),
             PyGUI.Radio("ST", group_id="wp_type", disabled=True)],
            [PyGUI.Radio("IP", group_id="wp_type", disabled=True),
             PyGUI.Radio("DP", group_id="wp_type", disabled=True),
             PyGUI.Radio("HA", group_id="wp_type", disabled=True)],
            [PyGUI.Button("Quick Capture", disabled=self.capture_button_disabled, key="quick_capture", pad=(5, (3, 8))),
             PyGUI.Text("Sequence:", pad=((0, 1), 3), key="sequence_text", auto_size_text=False, size=(8, 1)),
             PyGUI.Combo(values=("None", 1, 2, 3), default_value="None",
                         auto_size_text=False, size=(5, 1), readonly=True,
                         key="sequence")]
        ]

        frameactypelayout = [
            [
                PyGUI.Radio("F/A-18C", group_id="ac_type", default=True, key="hornet", enable_events=True),
                PyGUI.Radio("F-14A/B", group_id="ac_type", disabled=True, key="tomcat", enable_events=True),
                PyGUI.Radio("M-2000C", group_id="ac_type", disabled=True, key="mirage", enable_events=True),
                PyGUI.Radio("A-10C", group_id="ac_type", disabled=True, key="warthog", enable_events=True),
                PyGUI.Radio("AV-8B", group_id="ac_type", disabled=True, key="harrier", enable_events=True)
            ]
        ]

        framelongitude = PyGUI.Frame("Longitude", [[PyGUI.Column(longitude_col1), PyGUI.Column(longitude_col2),
                                                    PyGUI.Column(longitude_col3)]])
        framelatitude = PyGUI.Frame("Latitude", [[PyGUI.Column(latitude_col1), PyGUI.Column(latitude_col2),
                                                  PyGUI.Column(latitude_col3)]])
        frameelevation = PyGUI.Frame("Elevation", frameelevationlayout, pad=(5, (3, 10)))
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

                     [PyGUI.Text(self.capture_status, key="capture_status", auto_size_text=False, size=(20, 1))],
                 ]
             )
             ],

        ]

        frameposition = PyGUI.Frame("Position", framepositionlayout)
        framedata = PyGUI.Frame("Data", framedatalayoutcol2)
        framewptype = PyGUI.Frame("Waypoint Type", framewptypelayout)

        col0 = [
            [PyGUI.Text("Select profile:")],
            [PyGUI.Combo(values=[""] + self.editor.get_profile_names(), readonly=True,
                         enable_events=True, key='profileSelector', size=(27, 1))],
            [PyGUI.Listbox(values=list(), size=(30, 24), enable_events=True, key='activesList')],
            [PyGUI.Button("Add", size=(26, 1))],
            [PyGUI.Button("Remove", size=(26, 1))],
            [PyGUI.Button("Save profile", size=(12, 1)), PyGUI.Button("Delete profile", size=(12, 1))],
            [PyGUI.Button("Export to file", size=(12, 1)), PyGUI.Button("Import from file", size=(12, 1))],
            [PyGUI.Text(f"Version: {self.software_version}")]
        ]

        col1 = [
            [PyGUI.Text("Select preset location")],
            [PyGUI.Combo(values=[""] + [base.name for _, base in self.editor.default_bases.items()], readonly=False,
                         enable_events=True, key='baseSelector'),
             PyGUI.Button(button_text="F", key="filter")],
            [framedata, framewptype],
            [frameposition],
            [frameactype],
            [PyGUI.Button("Enter into aircraft", key="enter")],
        ]

        colmain1 = [
            [PyGUI.Column(col1)],
        ]

        layout = [
            [PyGUI.Column(col0), PyGUI.Column(colmain1)],
        ]

        return PyGUI.Window('DCS Waypoint Editor', layout)

    def set_sequence_station_selector(self, mode):
        if mode == "sequence":
            self.window.Element("sequence_text").Update(value="Sequence:")
            self.window.Element("sequence").Update(values=("None", 1, 2, 3), value="None")
        elif mode == "station":
            self.window.Element("sequence_text").Update(value="    Station:")
            self.window.Element("sequence").Update(values=(2, 3, 7, 8), value=2)

    def update_position(self, position=None, elevation=None, name=None, update_mgrs=True, aircraft=None):

        if position is not None:
            latdeg = round(position.lat.degree)
            latmin = round(position.lat.minute)
            latsec = round(position.lat.second, 2)

            londeg = round(position.lon.degree)
            lonmin = round(position.lon.minute)
            lonsec = round(position.lon.second, 2)
            mgrs_str = mgrs.encode(mgrs.LLtoUTM(position.lat.decimal_degree, position.lon.decimal_degree), 5)
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
        self.window.Element("elevMeters").Update(round(elevation/3.281) if type(elevation) == int else "")
        if aircraft is not None:
            self.window.Element(aircraft).Update(value=True)

        if update_mgrs:
            self.window.Element("mgrs").Update(mgrs_str)
        self.window.Refresh()

        if type(name) == str:
            self.window.Element("msnName").Update(name)
        else:
            self.window.Element("msnName").Update("")

    def update_waypoints_list(self):
        values = list()
        wp_types_limits = dict(
            hornet=dict(WP=None, MSN=6),
            tomcat=dict(WP=3, FP=1, ST=1, IP=1, DP=1, HA=1)
        )

        for wp_type, wp_list in self.profile.waypoints.items():

            if type(wp_list) == list:
                for i, waypoint in enumerate(wp_list):
                    namestr = f"{wp_type}{i+1}"

                    if waypoint.sequence:
                        namestr += f" | SEQ{waypoint.sequence}"

                    if waypoint.name:
                        namestr += f" | {waypoint.name}"

                    if wp_type not in wp_types_limits[self.profile.aircraft] or \
                            (wp_types_limits[self.profile.aircraft][wp_type] is not None
                             and i + 1 > wp_types_limits[self.profile.aircraft][wp_type]):
                        namestr = strike(namestr)

                    values.append(namestr)

            elif type(wp_list) == dict:
                for station, station_msns in wp_list.items():
                    for i, msn in enumerate(station_msns):
                        namestr = f"MSN{i + 1}"
                        namestr += f" | STA {station}"

                        if msn.name:
                            namestr += f" | {msn.name}"

                        if "MSN" not in wp_types_limits[self.profile.aircraft]\
                                or i + 1 > wp_types_limits[self.profile.aircraft]["MSN"]:
                            namestr = strike(namestr)
                        values.append(namestr)

        self.window.Element('activesList').Update(values=values)

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
        wpadded = False
        if name is None:
            name = str()

        try:
            if self.values["MSN"]:
                station = self.values.get("sequence", 0)
                mission = Wp(position=position, elevation=int(elevation) or 0, name=name, wp_type="MSN",
                             station=station)
                stations = self.profile.waypoints.get("MSN", dict())
                station_msns = stations.get(station, list())
                station_msns.append(mission)
                stations[station] = station_msns
                self.profile.waypoints["MSN"] = stations
                wpadded = True

            elif self.values["WP"]:
                sequence = self.values["sequence"]
                if sequence == "None":
                    sequence = 0
                else:
                    sequence = int(sequence)

                if sequence and len(self.profile.get_sequence(sequence)) >= 15:
                    return False

                waypoint = Wp(position, elevation=int(elevation or 0), name=name, sequence=sequence, wp_type="WP")
                profile_waypoints = self.profile.waypoints.get("WP", list())
                profile_waypoints.append(waypoint)
                self.profile.waypoints["WP"] = profile_waypoints

                if sequence not in self.profile.sequences:
                    self.profile.sequences.append(sequence)

                wpadded = True

            if wpadded:
                self.update_waypoints_list()
        except ValueError:
            PyGUI.Popup("Error: missing data or invalid data format")

        return wpadded

    def capture_map_coords(self):
        self.logger.debug("Attempting to capture map coords")
        image = ImageGrab.grab((101, 5, 101 + 269, 5 + 27))
        enhancer = ImageEnhance.Contrast(image)
        captured_map_coords = pytesseract.image_to_string(ImageOps.invert(enhancer.enhance(3)))
        if self.editor.settings.getboolean("PREFERENCES", "log_raw_tesseract_output"):
            self.logger.info("Raw captured text: " + captured_map_coords)
        return captured_map_coords

    def parse_map_coords_string(self, coords_string):
        split_string = coords_string.split(',')

        if "-" in split_string[0]:
            # dd mm ss.ss
            split_latlon = split_string[0].split(' ')
            lat_string = split_latlon[0].replace('N', '').replace('S', "-")
            lon_string = split_latlon[1].replace('£', 'E').replace('E', '').replace('W', "-")
            position = string2latlon(lat_string, lon_string, format_str="d%-%m%-%S")
        elif "°" not in split_string[0]:
            # mgrs
            mgrs_string = split_string[0].replace(" ", "")
            decoded_mgrs = mgrs.UTMtoLL(mgrs.decode(mgrs_string))
            position = LatLon(Latitude(degree=decoded_mgrs["lat"]), Longitude(degree=decoded_mgrs["lon"]))
        else:
            raise ValueError(f"Invalid coordinate format: {split_string[0]}")

        elevation = split_string[1].replace(' ', '')
        if "ft" in elevation:
            elevation = int(elevation.replace("ft", ""))
        elif "m" in elevation:
            elevation = round(int(elevation.replace("m", ""))*3.281)
        else:
            raise ValueError("Unable to parse elevation: " + elevation)

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
            self.logger.debug("Parsed text as coords succesfully: " + str(position))
        except (IndexError, ValueError, TypeError):
            self.logger.error("Failed to parse captured text", exc_info=True)
            self.window.Element('capture_status').Update("Status: Failed to capture")
        finally:
            self.enable_coords_input()
            self.window.Element('quick_capture').Update(disabled=False)
            self.window.Element('capture').Update(text="Capture from DCS F10 map")
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
                    self.window.Element("elevFeet").Update(round(int(elevation)*3.281))
                else:
                    self.window.Element("elevFeet").Update("")
            except ValueError:
                pass
        elif elevation_unit == "meters":
            elevation = self.window.Element("elevFeet").Get()
            try:
                if elevation:
                    self.window.Element("elevMeters").Update(round(int(elevation)/3.281))
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

            elevation = self.window.Element("elevFeet").Get()
            name = self.window.Element("msnName").Get()
            return position, elevation, name
        except ValueError as e:
            self.logger.error(f"Failed to validate coords: {e}")
            return None, None, None

    def update_profiles_list(self, name):
        profiles = self.editor.get_profile_names()
        self.window.Element("profileSelector").Update(values=[""] + profiles,
                                                      set_to_index=profiles.index(name) + 1)

    def run(self):
        while True:
            event, self.values = self.window.Read()
            self.logger.debug("Event: " + str(event))
            self.logger.debug("Values: " + str(self.values))

            if event is None or event == 'Exit':
                self.logger.info("Exiting...")
                break

            elif event == "Add":
                position, elevation, name = self.validate_coords()
                if position is not None:
                    self.add_waypoint(position, elevation, name)

            elif event == "Remove":
                if self.values['activesList']:
                    valuestr = self.values['activesList'][0]

                    if "MSN" not in valuestr:
                        i, = re.findall("(\\d)+", valuestr)
                        self.profile.waypoints.get("WP", list()).pop(int(i)-1)
                    else:
                        i, station = re.findall("(\\d)+", valuestr)
                        self.profile.waypoints.get("MSN", list())[int(station)].pop(int(i)-1)

                    self.update_waypoints_list()

            elif event == "activesList":
                if self.values['activesList']:
                    valuestr = self.values['activesList'][0]

                    if "MSN" not in valuestr:
                        i, = re.findall("(\\d)+", valuestr)
                        mission = self.profile.waypoints["WP"][int(i) - 1]

                    else:
                        i, station = re.findall("(\\d)+", valuestr)
                        mission = self.profile.waypoints["MSN"][int(station)][int(i) - 1]

                    self.update_position(mission.position, mission.elevation, mission.name)

            elif event == "Save profile":
                if self.profile.waypoints:
                    name = self.profile.profilename
                    if not name:
                        name = PyGUI.PopupGetText("Enter profile name", "Saving profile")

                    if not name:
                        continue

                    self.profile.save(name)
                    self.update_profiles_list(name)

            elif event == "Delete profile":
                if not self.profile.profilename:
                    continue

                self.profile.delete()
                profiles = self.editor.get_profile_names()
                self.window.Element("profileSelector").Update(values=[""] + profiles)
                self.profile = self.editor.get_profile("")
                self.update_waypoints_list()
                self.update_position()

            elif event == "profileSelector":
                try:
                    self.profile = self.editor.get_profile(self.values['profileSelector'])
                    self.update_waypoints_list()

                except DoesNotExist:
                    PyGUI.Popup("Profile not found")

            elif event == "Export to file":
                e = dict(waypoints=[waypoint.to_dict() for waypoint
                                    in self.profile.waypoints_as_list + self.profile.msns_as_list],
                         name=self.profile.profilename, aircraft=self.profile.aircraft)

                filename = PyGUI.PopupGetFile("Enter file name", "Exporting profile", default_extension=".json",
                                              save_as=True, file_types=(("JSON File", "*.json"),))

                if filename is None:
                    continue

                with open(filename + ".json", "w+") as f:
                    json.dump(e, f, indent=4)

            elif event == "Import from file":
                filename = PyGUI.PopupGetFile("Enter file name", "Importing profile")

                if filename is None:
                    continue

                with open(filename, "r") as f:
                    d = json.load(f)

                self.profile = self.editor.get_profile("")
                self.profile.aircraft = d.get('aircraft', "hornet")

                waypoints = dict()
                waypoints_list = d.get('waypoints', list())
                for wp in waypoints_list:
                    wp_object = Wp(position=LatLon(Latitude(wp['latitude']), Longitude(wp['longitude'])),
                                   name=wp.get("name", ""),
                                   elevation=wp['elevation'],
                                   sequence=wp.get("sequence", 0),
                                   wp_type=wp.get("wp_type", "WP"),
                                   station=wp.get("station", 0))

                    if wp.get("wp_type") != "MSN":
                        wp_type_list = waypoints.get(wp.get("wp_type", "WP"), list())
                        wp_type_list.append(wp_object)
                        waypoints[wp.get("wp_type", "WP")] = wp_type_list
                    else:
                        stations = waypoints.get("MSN", dict())
                        station = stations.get(wp_object.station, list())
                        station.append(wp_object)
                        stations[wp_object.station] = station
                        waypoints["MSN"] = stations

                self.profile.waypoints = waypoints
                self.update_waypoints_list()

                if d.get("name", ""):
                    self.profile.save(d.get("name"))
                    self.update_profiles_list(d.get("name"))

            elif event == "capture":
                if not self.capturing:
                    self.disable_coords_input()
                    self.window.Element('capture').Update(text="Stop capturing")
                    self.window.Element('quick_capture').Update(disabled=True)
                    self.window.Element('capture_status').Update("Status: Capturing...")
                    self.window.Refresh()
                    keyboard.add_hotkey(self.capture_key, self.input_parsed_coords, timeout=1)
                    self.capturing = True
                else:
                    self.stop_quick_capture()

            elif event == "quick_capture":
                self.exit_quick_capture = False
                self.disable_coords_input()
                self.window.Element('capture').Update(text="Stop capturing")
                self.window.Element('quick_capture').Update(disabled=True)
                self.window.Element('capture_status').Update("Status: Capturing...")
                self.capturing = True
                self.window.Refresh()
                keyboard.add_hotkey(self.capture_key, self.add_wp_parsed_coords, timeout=1)

            elif event == "baseSelector":
                base = self.editor.default_bases.get(self.values['baseSelector'])

                if base is not None:
                    self.update_position(base.position, base.elevation, base.name)

            elif event == "enter":
                self.profile.aircraft = "hornet"
                self.window.Element('enter').Update(disabled=True)
                self.editor.enter_all(self.profile)
                self.window.Element('enter').Update(disabled=False)

            elif event == "WP":
                self.set_sequence_station_selector("sequence")

            elif event in "MSN":
                self.set_sequence_station_selector("station")

            elif event == "elevFeet":
                self.update_altitude_elements("meters")

            elif event == "elevMeters":
                self.update_altitude_elements("feet")

            elif event in ("latDeg", "latMin", "latSec", "lonDeg", "lonMin", "lonSec"):
                position, _, _ = self.validate_coords()

                if position is not None:
                    m = mgrs.encode(mgrs.LLtoUTM(position.lat.decimal_degree, position.lon.decimal_degree), 5)
                    self.window.Element("mgrs").Update(m)

            elif event == "mgrs":
                mgrs_string = self.window.Element("mgrs").Get()
                try:
                    decoded_mgrs = mgrs.UTMtoLL(mgrs.decode(mgrs_string))
                    position = LatLon(Latitude(degree=decoded_mgrs["lat"]), Longitude(degree=decoded_mgrs["lon"]))
                    self.update_position(position, update_mgrs=False)
                except (TypeError, ValueError) as e:
                    self.logger.error(f"Failed to decode MGRS: {e}")

            elif event in ("hornet", "tomcat", "harrier", "warthog", "mirage"):
                self.profile.aircraft = event
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
        self.editor.db.close()

