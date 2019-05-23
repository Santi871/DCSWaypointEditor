import PySimpleGUI as PyGUI
from peewee import DoesNotExist
from objects import MSN, Wp
from LatLon23 import LatLon, Longitude, Latitude, string2latlon
import json
import folium
import webbrowser
import os
from PIL import ImageGrab, ImageEnhance, ImageOps
import pytesseract
import keyboard


pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


class GUI:
    def __init__(self, editor):
        self.editor = editor
        self.current_missions = list()
        self.current_waypoints = list()
        self.captured_map_coords = str()
        self.window = self.create_gui()

    def create_gui(self):
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
            [PyGUI.Radio("WP", group_id="wp_type", default=True, enable_events=True),
             PyGUI.Radio("MSN", group_id="wp_type", enable_events=True),
             PyGUI.Radio("FP", group_id="wp_type", disabled=True), PyGUI.Radio("ST", group_id="wp_type",
                                                                               disabled=True)],
            [PyGUI.Radio("IP", group_id="wp_type", disabled=True), PyGUI.Radio("DP", group_id="wp_type", disabled=True),
             PyGUI.Radio("HA", group_id="wp_type", disabled=True)],
        ]

        frameactypelayout = [
            [PyGUI.Radio("F/A-18C", group_id="ac_type", default=True), PyGUI.Radio("F-14A/B", group_id="ac_type",
                                                                                   disabled=True),
             PyGUI.Radio("M-2000C", group_id="ac_type", disabled=True), PyGUI.Radio("A-10C", group_id="ac_type",
                                                                                    disabled=True)],
        ]

        framelongitude = PyGUI.Frame("Longitude", [[PyGUI.Column(longitude_col1), PyGUI.Column(longitude_col2),
                                                    PyGUI.Column(longitude_col3)]])
        framelatitude = PyGUI.Frame("Latitude", [[PyGUI.Column(latitude_col1), PyGUI.Column(latitude_col2),
                                                  PyGUI.Column(latitude_col3)]])
        frameelevation = PyGUI.Frame("Elevation", frameelevationlayout, pad=(5, (3, 10)))

        framepositionlayout = [
            [framelatitude],
            [framelongitude],
            [frameelevation,
             PyGUI.Column([[PyGUI.Button("Capture from DCS F10 map", key="capture",
                                         pad=(1, (18, 3)))], [PyGUI.Text("Status: Not capturing", key="capture_status",
                                                                         auto_size_text=False, size=(20, 1))]])]
        ]

        frameposition = PyGUI.Frame("Position", framepositionlayout)
        framedata = PyGUI.Frame("Data", framedatalayoutcol2)
        framewptype = PyGUI.Frame("Waypoint Type", framewptypelayout)
        frameactype = PyGUI.Frame("Aircraft Type", frameactypelayout)

        col0 = [
            [PyGUI.Text("Status: ")],
            [PyGUI.Listbox(values=list(), size=(30, 24), enable_events=True, key='activesList')],
            [PyGUI.Button("Add", size=(26, 1))],
            [PyGUI.Button("Save profile", size=(12, 1)), PyGUI.Button("Load profile", size=(12, 1))],
            [PyGUI.Button("Export to file", size=(12, 1)), PyGUI.Button("Import from file", size=(12, 1))],
        ]

        col1 = [
            [PyGUI.Text("Select airfield/BlueFlag FARP")],
            [PyGUI.Combo(values=[base.name for _, base in self.editor.default_bases.items()], readonly=True,
                         enable_events=True, key='baseSelector')],
            [framedata],
            [frameposition],
            [framewptype],
            [frameactype],
            [PyGUI.Button("Open map in browser", key="map"), PyGUI.Button("Enter into AC", key="enter")],
        ]

        colmain1 = [
            [PyGUI.Column(col1)],
        ]

        layout = [
            [PyGUI.Column(col0), PyGUI.Column(colmain1)],
        ]

        return PyGUI.Window('Waypoint Editor', layout)

    def update_position(self, position, elevation, name=None):
        self.window.Element("latDeg").Update(round(position.lat.degree))
        self.window.Element("latMin").Update(round(position.lat.minute))
        self.window.Element("latSec").Update(round(position.lat.second, 2))

        self.window.Element("lonDeg").Update(round(position.lon.degree))
        self.window.Element("lonMin").Update(round(position.lon.minute))
        self.window.Element("lonSec").Update(round(position.lon.second, 2))

        self.window.Element("elevFeet").Update(round(elevation))
        self.window.Element("capture_status").Update("Status: Not capturing")
        self.window.Refresh()

        if type(name) == str:
            self.window.Element("msnName").Update(name)
        else:
            self.window.Element("msnName").Update("")

    def update_waypoints_list(self):
        values = list()

        i = 1
        for mission in self.current_missions:
            namestr = f"MSN{i}"
            if mission.name:
                namestr += f" | {mission.name}"
            values.append(namestr)
            i += 1

        i = 1
        for waypoint in self.current_waypoints:
            namestr = f"WP{i}"
            if waypoint.name:
                namestr += f" | {waypoint.name}"
            values.append(namestr)
            i += 1

        self.window.Element('activesList').Update(values=values)

    def capture_map_coords(self):
        image = ImageGrab.grab((101, 5, 101 + 269, 5 + 27))
        enhancer = ImageEnhance.Contrast(image)
        self.captured_map_coords = pytesseract.image_to_string(ImageOps.invert(enhancer.enhance(3)))
        print("Recstr: " + self.captured_map_coords)

    def parse_map_coords_string(self, coords_string):
        split_string = coords_string.split(',')
        split_latlon = split_string[0].split(' ')
        lat_string = split_latlon[0].replace('N', '').replace('S', "-")
        lon_string = split_latlon[1].replace('£', 'E').replace('E', '').replace('W', "-")

        position = string2latlon(lat_string, lon_string, format_str="d%-%m%-%S")
        elevation = int(split_string[1].replace(' ', '').replace('ft', ''))
        self.captured_map_coords = str()
        return position, elevation

    def run(self):
        while True:
            event, values = self.window.Read()
            print(str(event))
            print(str(values))

            if event is None or event == 'Exit':
                break

            elif event == "Add":
                lat_deg = self.window.Element("latDeg").Get()
                lat_min = self.window.Element("latMin").Get()
                lat_sec = self.window.Element("latSec").Get()

                lon_deg = self.window.Element("lonDeg").Get()
                lon_min = self.window.Element("lonMin").Get()
                lon_sec = self.window.Element("lonSec").Get()

                elevation = self.window.Element("elevFeet").Get()
                name = self.window.Element("msnName").Get()

                if values[1] and len(self.current_missions) < 6:

                    try:
                        mission = MSN(LatLon(Latitude(degree=lat_deg, minute=lat_min, second=lat_sec),
                                             Longitude(degree=lon_deg, minute=lon_min, second=lon_sec)),
                                      elevation=int(elevation or 0), number=len(self.current_missions) + 1, name=name)
                        self.current_missions.append(mission)
                    except ValueError:
                        PyGUI.Popup("Error: missing data or invalid data format")

                elif event == "Add mission" and len(self.current_missions) == 6:
                    PyGUI.Popup("Error: maximum number of missions reached", keep_on_top=True)

                elif values[0]:
                    try:
                        waypoint = Wp(LatLon(Latitude(degree=lat_deg, minute=lat_min, second=lat_sec),
                                             Longitude(degree=lon_deg, minute=lon_min, second=lon_sec)),
                                      elevation=int(elevation or 0), name=name)
                        self.current_waypoints.append(waypoint)
                    except ValueError:
                        PyGUI.Popup("Error: missing data or invalid data format")

                self.update_waypoints_list()

            elif event == "activesList":
                ei = values['activesList'][0].find(' ')

                if ei != -1:
                    valuestr = values['activesList'][0][:ei]
                else:
                    valuestr = values['activesList'][0]

                if "WP" in valuestr:
                    i = int(valuestr[2:])
                    mission = self.current_waypoints[i - 1]
                else:
                    i = int(valuestr[3:])
                    mission = self.current_missions[i - 1]

                self.update_position(mission.position, mission.elevation, mission.name)

            elif event == "Save profile":
                name = PyGUI.PopupGetText("Enter profile name", "Saving profile")
                self.editor.save_profile(name, self.current_missions, self.current_waypoints)

            elif event == "Load profile":
                name = PyGUI.PopupGetText("Enter profile name", "Loading profile")
                try:
                    self.current_missions, self.current_waypoints = self.editor.get_profile(name)
                    self.update_waypoints_list()
                except DoesNotExist:
                    PyGUI.Popup("Profile not found")

            elif event == "Export to file":
                e = dict(missions=[mission.to_dict() for mission in self.current_missions],
                         waypoints=[waypoint.to_dict() for waypoint in self.current_waypoints])

                filename = PyGUI.PopupGetText("Enter file name", "Exporting profile")

                with open(filename + ".json", "w+") as f:
                    json.dump(e, f)

            elif event == "Import from file":
                filename = PyGUI.PopupGetFile("Enter file name", "Importing profile")

                if filename is None:
                    continue

                with open(filename, "r") as f:
                    d = json.load(f)

                self.current_missions = [MSN(position=LatLon(Latitude(mission['latitude']),
                                                             Longitude(mission['longitude'])),
                                             name=mission['name'], elevation=mission['elevation'],
                                             number=mission['number']) for mission in d.get('missions', list())]
                self.current_waypoints = [
                    Wp(position=LatLon(Latitude(waypoint['latitude']), Longitude(waypoint['longitude'])),
                       name=waypoint['name'],
                       elevation=waypoint['elevation']) for waypoint in d.get('waypoints', list())]

                self.update_waypoints_list()
            elif event == "map":
                if not self.current_waypoints and not self.current_missions:
                    continue

                lats = [waypoint.position.lat.degree for waypoint in self.current_waypoints] + \
                       [mission.position.lat.degree for mission in self.current_missions]

                lons = [waypoint.position.lon.degree for waypoint in self.current_waypoints] + \
                       [mission.position.lon.degree for mission in self.current_missions]

                m = folium.Map(location=[(max(lats) + min(lats)) / 2, (max(lons) + min(lons)) / 2], zoom_start=6)

                for waypoint in self.current_waypoints:
                    folium.Marker((waypoint.position.lat.decimal_degree, waypoint.position.lon.decimal_degree),
                                  tooltip=waypoint.name or None).add_to(m)

                for mission in self.current_missions:
                    folium.Marker((mission.position.lat.decimal_degree, mission.position.lon.decimal_degree),
                                  tooltip=mission.name or None).add_to(m)

                m.save("map.html")
                directory = os.getcwd()
                webbrowser.open(directory + "\\map.html")

            elif event == "capture":
                self.window.Element('capture').Update(disabled=True)
                self.window.Element('capture_status').Update("Status: Capturing...")
                self.window.Refresh()
                keyboard.add_hotkey("ctrl+t", self.capture_map_coords, timeout=1)
                keyboard.wait("ctrl+t")

                try:
                    position, elevation = self.parse_map_coords_string(self.captured_map_coords)
                    self.update_position(position, elevation)
                    self.window.Element('capture_status').Update("Status: Captured")
                except (IndexError, ValueError):
                    self.captured_map_coords = str()
                    self.window.Element('capture_status').Update("Status: Failed to capture")
                    continue
                finally:
                    self.window.Element('capture').Update(disabled=False)

            elif event == "baseSelector":
                base = self.editor.default_bases[values['baseSelector']]
                self.update_position(base.position, base.elev, base.name)

            elif event == "enter":
                self.window.Element('enter').Update(disabled=True)
                self.editor.enter_all(self.current_missions, self.current_waypoints)
                self.window.Element('enter').Update(disabled=False)

        try:
            keyboard.remove_hotkey('ctrl+t')
        except KeyError:
            pass

        self.editor.db.close()
        exit(0)
