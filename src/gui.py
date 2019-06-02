import PySimpleGUI as PyGUI
from peewee import DoesNotExist
from src.objects import MSN, Wp
from src.logger import get_logger
from LatLon23 import LatLon, Longitude, Latitude, string2latlon
import json
from PIL import ImageGrab, ImageEnhance, ImageOps
import pytesseract
import keyboard
from pathlib import Path
import os


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


class GUI:
    def __init__(self, editor):
        self.logger = get_logger("gui")
        self.editor = editor
        self.captured_map_coords = None
        self.profile = self.editor.get_profile('')
        self.exit_quick_capture = False
        self.values = None
        self.capturing = False
        self.capture_key = self.editor.settings.get("PREFERENCES", "capture_key")

        pytesseract.pytesseract.tesseract_cmd = self.editor.settings['PREFERENCES'].get('tesseract_path', str())
        try:
            self.tesseract_version = pytesseract.get_tesseract_version()
            self.capture_status = "Status: Not capturing"
            self.capture_button_disabled = False
        except pytesseract.pytesseract.TesseractNotFoundError:
            self.tesseract_version = None
            self.capture_status = "Status: Tesseract not found"
            self.capture_button_disabled = True

        self.window = self.create_gui()

    def exit_capture(self):
        self.exit_quick_capture = True

    def create_gui(self):
        self.logger.debug("Creating GUI")

        latitude_col1 = [
            [PyGUI.Text("Degrees")],
            [PyGUI.InputText(size=(10, 1), key="latDeg")],
        ]

        latitude_col2 = [
            [PyGUI.Text("Minutes")],
            [PyGUI.InputText(size=(10, 1), key="latMin")],
        ]

        latitude_col3 = [
            [PyGUI.Text("Seconds")],
            [PyGUI.InputText(size=(10, 1), key="latSec", pad=(5, (3, 10)))],
        ]

        longitude_col1 = [
            [PyGUI.Text("Degrees")],
            [PyGUI.InputText(size=(10, 1), key="lonDeg")],
        ]

        longitude_col2 = [
            [PyGUI.Text("Minutes")],
            [PyGUI.InputText(size=(10, 1), key="lonMin")],
        ]

        longitude_col3 = [
            [PyGUI.Text("Seconds")],
            [PyGUI.InputText(size=(10, 1), key="lonSec", pad=(5, (3, 10)))],
        ]

        frameelevationlayout = [
            [PyGUI.Text("Feet")],
            [PyGUI.InputText(size=(20, 1), key="elevFeet", pad=(5, (3, 10)))],
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
            [PyGUI.Radio("IP", group_id="wp_type", disabled=True), PyGUI.Radio("DP", group_id="wp_type", disabled=True),
             PyGUI.Radio("HA", group_id="wp_type", disabled=True)],
            [PyGUI.Button("Quick Capture", disabled=self.capture_button_disabled, key="quick_capture", pad=(5, (3, 8))),
             PyGUI.Text("Sequence:", pad=((0, 1), 3)),
             PyGUI.Combo(values=("None", 1, 2, 3), default_value="None",
                         auto_size_text=False, size=(5, 1), readonly=True,
                         key="sequence")]
        ]

        frameactypelayout = [
            [PyGUI.Radio("F/A-18C", group_id="ac_type", default=True), PyGUI.Radio("F-14A/B", group_id="ac_type",
                                                                                   disabled=True),
             PyGUI.Radio("M-2000C", group_id="ac_type", disabled=True), PyGUI.Radio("A-10C", group_id="ac_type",
                                                                                    disabled=True),
             PyGUI.Radio("AV-8B", group_id="ac_type", disabled=True)],
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
             PyGUI.Column([[PyGUI.Button("Capture from DCS F10 map", disabled=self.capture_button_disabled,
                                         key="capture",
                                         pad=(1, (18, 3)))], [PyGUI.Text(self.capture_status, key="capture_status",
                                                                         auto_size_text=False, size=(20, 1))]])],
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
        ]

        col1 = [
            [PyGUI.Text("Select preset location")],
            [PyGUI.Combo(values=[""] + [base.name for _, base in self.editor.default_bases.items()], readonly=True,
                         enable_events=True, key='baseSelector')],
            [framedata, framewptype],
            [frameposition],
            [frameactype],
            [PyGUI.Button("Open map in browser", key="map", visible=False),
             PyGUI.Button("Enter into aircraft", key="enter")],
        ]

        colmain1 = [
            [PyGUI.Column(col1)],
        ]

        layout = [
            [PyGUI.Column(col0), PyGUI.Column(colmain1)],
        ]

        return PyGUI.Window('DCS Waypoint Editor', layout)

    def update_position(self, position=None, elevation=None, name=None):

        if position is not None:
            latdeg = round(position.lat.degree)
            latmin = round(position.lat.minute)
            latsec = round(position.lat.second, 2)

            londeg = round(position.lon.degree)
            lonmin = round(position.lon.minute)
            lonsec = round(position.lon.second, 2)
        else:
            latdeg = ""
            latmin = ""
            latsec = ""

            londeg = ""
            lonmin = ""
            lonsec = ""

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
        self.window.Refresh()

        if type(name) == str:
            self.window.Element("msnName").Update(name)
        else:
            self.window.Element("msnName").Update("")

    def update_waypoints_list(self):
        values = list()

        i = 1
        for mission in self.profile.missions:
            namestr = f"MSN{i}"
            if mission.name:
                namestr += f" | {mission.name}"
            values.append(namestr)
            i += 1

        i = 1
        for waypoint in self.profile.waypoints:
            namestr = f"WP{i}"
            if waypoint.sequence:
                namestr += f" | SEQ{waypoint.sequence}"

            if waypoint.name:
                namestr += f" | {waypoint.name}"

            values.append(namestr)
            i += 1

        self.window.Element('activesList').Update(values=values)

    def add_waypoint(self, position, elevation, name=None):
        max_missions = 6

        wpadded = False
        if name is None:
            name = str()

        try:
            if self.values["MSN"] and len(self.profile.missions) < max_missions:
                mission = MSN(position=position, elevation=int(elevation) or 0)
                self.profile.missions.append(mission)
                wpadded = True

            elif self.values["WP"]:
                sequence = self.values["sequence"]
                if sequence == "None":
                    sequence = 0
                else:
                    sequence = int(sequence)

                if sequence and len(self.profile.get_sequence(sequence)) >= 15:
                    return False

                waypoint = Wp(position, elevation=int(elevation or 0), name=name, sequence=sequence)
                self.profile.waypoints.append(waypoint)

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
        self.logger.info("Raw captured text: " + captured_map_coords)
        return captured_map_coords

    def parse_map_coords_string(self, coords_string):
        split_string = coords_string.split(',')
        split_latlon = split_string[0].split(' ')
        lat_string = split_latlon[0].replace('N', '').replace('S', "-")
        lon_string = split_latlon[1].replace('£', 'E').replace('E', '').replace('W', "-")

        position = string2latlon(lat_string, lon_string, format_str="d%-%m%-%S")
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
        captured_coords = self.capture_map_coords()
        try:
            position, elevation = self.parse_map_coords_string(captured_coords)
            self.update_position(position, elevation)
            self.window.Element('capture_status').Update("Status: Captured")
            self.logger.debug("Parsed text as coords succesfully: " + str(position))
        except (IndexError, ValueError):
            self.logger.error("Failed to parse captured text", exc_info=True)
            self.window.Element('capture_status').Update("Status: Failed to capture")
        finally:
            self.window.Element('quick_capture').Update(disabled=False)
            self.window.Element('capture').Update(text="Capture from DCS F10 map")
            self.window.Element('capture_status').Update("Status: Not capturing")
            self.capturing = False

        keyboard.remove_hotkey(self.capture_key)

    def add_wp_parsed_coords(self):
        captured_coords = self.capture_map_coords()
        try:
            position, elevation = self.parse_map_coords_string(captured_coords)
        except (IndexError, ValueError):
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

        self.window.Element('capture').Update(text="Capture from DCS F10 map")
        self.window.Element('quick_capture').Update(disabled=False)
        self.window.Element('capture_status').Update("Status: Not capturing")
        self.capturing = False

    def run(self):
        while True:
            event, self.values = self.window.Read()
            self.logger.debug("Event: " + str(event))
            self.logger.debug("Values: " + str(self.values))

            if event is None or event == 'Exit':
                self.logger.info("Exiting...")
                break

            elif event == "Add":
                lat_deg = self.window.Element("latDeg").Get()
                lat_min = self.window.Element("latMin").Get()
                lat_sec = self.window.Element("latSec").Get()

                lon_deg = self.window.Element("lonDeg").Get()
                lon_min = self.window.Element("lonMin").Get()
                lon_sec = self.window.Element("lonSec").Get()

                position = LatLon(Latitude(degree=lat_deg, minute=lat_min, second=lat_sec),
                                  Longitude(degree=lon_deg, minute=lon_min, second=lon_sec))
                elevation = self.window.Element("elevFeet").Get()
                name = self.window.Element("msnName").Get()

                self.add_waypoint(position, elevation, name)

            elif event == "Remove":
                if not len(self.values['activesList']):
                    continue
                ei = self.values['activesList'][0].find(' ')

                if ei != -1:
                    valuestr = self.values['activesList'][0][:ei]
                else:
                    valuestr = self.values['activesList'][0]

                if "WP" in valuestr:
                    i = int(valuestr[2:])
                    self.profile.waypoints.pop(i-1)
                else:
                    i = int(valuestr[3:])
                    self.profile.missions.pop(i-1)

                self.update_waypoints_list()

            elif event == "activesList":
                if not len(self.values['activesList']):
                    continue
                ei = self.values['activesList'][0].find(' ')

                if ei != -1:
                    valuestr = self.values['activesList'][0][:ei]
                else:
                    valuestr = self.values['activesList'][0]

                if "WP" in valuestr:
                    i = int(valuestr[2:])
                    mission = self.profile.waypoints[i - 1]

                else:
                    i = int(valuestr[3:])
                    mission = self.profile.missions[i - 1]

                self.update_position(mission.position, mission.elevation, mission.name)

            elif event == "Save profile":
                name = self.profile.profilename
                if not name:
                    name = PyGUI.PopupGetText("Enter profile name", "Saving profile")

                if not name:
                    return

                self.profile.save(name)
                profiles = self.editor.get_profile_names()
                self.window.Element("profileSelector").Update(values=[""] + profiles,
                                                              set_to_index=profiles.index(name)+1)

            elif event == "Delete profile":
                self.profile.delete()
                profiles = self.editor.get_profile_names()
                self.window.Element("profileSelector").Update(values=[""] + profiles)
                self.profile = self.editor.get_profile("")
                self.update_waypoints_list()

            elif event == "profileSelector":
                try:
                    self.profile = self.editor.get_profile(self.values['profileSelector'])
                    self.update_waypoints_list()
                    try:
                        first_waypoint = [*self.profile.waypoints, *self.profile.missions][0]
                        self.update_position(first_waypoint.position, first_waypoint.elevation, first_waypoint.name)
                    except IndexError:
                        self.update_position()

                except DoesNotExist:
                    PyGUI.Popup("Profile not found")

            elif event == "Export to file":
                e = dict(missions=[mission.to_dict() for mission in self.profile.missions],
                         waypoints=[waypoint.to_dict() for waypoint in self.profile.waypoints],
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

                self.profile = self.editor.get_profile(d.get('name', str()))
                self.profile.aircraft = d.get('aircraft')
                self.profile.missions = [MSN(position=LatLon(Latitude(mission['latitude']),
                                                             Longitude(mission['longitude'])),
                                             name=mission['name'], elevation=mission['elevation'])
                                         for mission in d.get('missions', list())]
                self.profile.waypoints = [
                    Wp(position=LatLon(Latitude(waypoint['latitude']), Longitude(waypoint['longitude'])),
                       name=waypoint['name'],
                       elevation=waypoint['elevation'],
                       sequence=waypoint['sequence']) for waypoint in d.get('waypoints', list())]

                self.update_waypoints_list()

            elif event == "map":
                # temporarily disabled
                """
                if not self.profile.waypoints and not self.profile.missions:
                    continue

                lats = [waypoint.position.lat.degree for waypoint in self.profile.waypoints] + \
                       [mission.position.lat.degree for mission in self.profile.missions]

                lons = [waypoint.position.lon.degree for waypoint in self.profile.waypoints] + \
                       [mission.position.lon.degree for mission in self.profile.missions]

                lines = list()
                for wp in self.profile.waypoints:
                    if wp.sequence:
                        lines.append([wp.position.lat.decimal_degree, wp.position.lon.decimal_degree])

                m = folium.Map(location=[(max(lats) + min(lats)) / 2, (max(lons) + min(lons)) / 2], zoom_start=6)

                if lines:
                    folium.PolyLine(lines).add_to(m)

                for waypoint in self.profile.waypoints:
                    folium.Marker((waypoint.position.lat.decimal_degree, waypoint.position.lon.decimal_degree),
                                  tooltip=waypoint.name or None).add_to(m)

                for mission in self.profile.missions:
                    folium.Marker((mission.position.lat.decimal_degree, mission.position.lon.decimal_degree),
                                  tooltip=mission.name or None).add_to(m)

                m.save("map.html")
                directory = os.getcwd()
                webbrowser.open(directory + "\\map.html")
                """
                pass

            elif event == "capture":
                if not self.capturing:
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
                self.window.Element('enter').Update(disabled=True)
                self.editor.enter_all(self.profile)
                self.window.Element('enter').Update(disabled=False)

            elif event == "WP":
                self.window.Element('sequence').Update(disabled=False)

            elif event in ("MSN",):
                self.window.Element('sequence').Update(disabled=True, set_to_index=0)

            self.close()

    def close(self):
        try:
            keyboard.remove_hotkey(self.capture_key)
        except KeyError:
            pass

        self.editor.db.close()
        self.editor.handler.press.p.s.close()
