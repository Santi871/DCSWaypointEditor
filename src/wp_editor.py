from time import sleep
from src.keybinds import BindsManager
from src.objects import default_bases, Profile
from src.db import DatabaseInterface
from src.logger import get_logger


def latlon_tostring(latlong, decimal_minutes_mode=False):

    if not decimal_minutes_mode:
        lat_deg = str(abs(round(latlong.lat.degree)))
        lat_min = str(abs(round(latlong.lat.minute))).zfill(2)
        lat_sec = abs(latlong.lat.second)

        lat_sec_int, lat_sec_dec = divmod(lat_sec, 1)

        lat_sec = str(int(lat_sec_int)).zfill(2)

        if lat_sec_dec:
            lat_sec += "." + str(round(lat_sec_dec, 2))[2:4]

        lon_deg = str(abs(round(latlong.lon.degree)))
        lon_min = str(abs(round(latlong.lon.minute))).zfill(2)
        lon_sec = abs(latlong.lon.second)

        lon_sec_int, lon_sec_dec = divmod(lon_sec, 1)

        lon_sec = str(int(lon_sec_int)).zfill(2)

        if lon_sec_dec:
            lon_sec += "." + str(round(lon_sec_dec, 2))[2:4]

        return lat_deg + lat_min + lat_sec, lon_deg + lon_min + lon_sec
    else:
        lat_deg = str(abs(round(latlong.lat.degree)))
        lat_min = str(round(latlong.lat.decimal_minute, 4))

        lat_min_split = lat_min.split(".")
        lat_min_split[0] = lat_min_split[0].zfill(2)
        lat_min = ".".join(lat_min_split)

        lon_deg = str(abs(round(latlong.lon.degree)))
        lon_min = str(round(latlong.lon.decimal_minute, 4))

        lon_min_split = lon_min.split(".")
        lon_min_split[0] = lon_min_split[0].zfill(2)
        lon_min = ".".join(lon_min_split)

        return lat_deg + lat_min, lon_deg + lon_min


class KeybindsInput:

    def __init__(self, settings):
        self.logger = get_logger("keybinds_input")
        self.settings = settings
        self.press = BindsManager("dcs-bios", self.logger, settings['PREFERENCES'])

    def enter_number(self, number, two_enters=False):
        for num in str(number):
            if num == ".":
                break

            self.press.ufc(num)

        self.press.ufc("ENT", delay_release=0.5)

        i = str(number).find(".")

        if two_enters:
            if i > 0 and str(number)[i + 1] != "0":
                for num in str(number)[str(number).find(".") + 1:]:
                    self.press.ufc(num)

            self.press.ufc("ENT", delay_release=0.5)

    def enter_coords(self, latlong, elev, pp, decimal_minutes_mode=False):
        lat_str, lon_str = latlon_tostring(latlong, decimal_minutes_mode=decimal_minutes_mode)

        if not pp:
            if latlong.lat.degree > 0:
                self.press.ufc("2", delay_release=0.5)
            else:
                self.press.ufc("8", delay_release=0.5)
            self.enter_number(lat_str, two_enters=True)
            sleep(0.5)

            if latlong.lon.degree > 0:
                self.press.ufc("6", delay_release=0.5)
            else:
                self.press.ufc("4", delay_release=0.5)
            self.enter_number(lon_str, two_enters=True)

            if elev:
                self.press.ufc("OSB3")
                self.press.ufc("OSB1")
                self.enter_number(elev)
        else:
            self.press.ufc("OSB1")
            if latlong.lat.degree > 0:
                self.press.ufc("2", delay_release=0.5)
            else:
                self.press.ufc("8", delay_release=0.5)
            self.enter_number(lat_str, two_enters=True)

            self.press.ufc("OSB3")

            if latlong.lon.degree > 0:
                self.press.ufc("6", delay_release=0.5)
            else:
                self.press.ufc("4", delay_release=0.5)

            self.enter_number(lon_str, two_enters=True)

            self.press.lmdi("14")
            self.press.lmdi("14")

            if elev:
                self.press.ufc("OSB4")
                self.press.ufc("OSB4")
                elev = round(float(elev) / 3.2808)
                self.enter_number(elev)

    def enter_waypoints(self, wps, sequences):
        if not wps:
            return

        i = 1
        self.press.ampcd("10")
        self.press.ampcd("19")
        self.press.ufc("CLR")
        self.press.ufc("CLR")

        for wp in wps:
            if not wp.name:
                self.logger.info(f"Entering waypoint {i}")
            else:
                self.logger.info(f"Entering waypoint {i} - {wp.name}")

            self.press.ampcd("12")
            self.press.ampcd("5")
            self.press.ufc("OSB1")
            self.enter_coords(wp.position, wp.elevation, pp=False, decimal_minutes_mode=True)
            self.press.ufc("CLR")

            i += 1

        for sequencenumber, waypointslist in sequences.items():
            if sequencenumber != 1:
                self.press.ampcd("15")
                self.press.ampcd("15")
            else:
                waypointslist = [0] + waypointslist

            self.press.ampcd("1")

            for waypoint in waypointslist:
                self.press.ufc("OSB4")
                self.press.ufc(waypoint)
                self.press.ufc("ENT")

        self.press.ufc("CLR")
        self.press.ufc("CLR")
        self.press.ufc("CLR")
        self.press.ampcd("19")
        self.press.ampcd("10")

    def enter_pp_msn(self, msn, n):
        if msn.name:
            self.logger.info(f"Entering PP mission {n} - {msn.name}")
        else:
            self.logger.info(f"Entering PP mission {n}")

        self.press.lmdi(f"{n + 5}")
        self.press.lmdi("14")
        self.press.ufc("OSB3")

        self.enter_coords(msn.position, msn.elevation, pp=True)

        self.press.ufc("CLR")
        self.press.ufc("CLR")

    def enter_missions(self, msns):
        if not msns:
            return

        self.press.lmdi("11")
        self.press.lmdi("4")

        n = 1
        for msn in msns:
            self.enter_pp_msn(msn, n)
            n += 1

        self.press.lmdi("6")
        self.press.lmdi("19")
        self.press.lmdi("6")


class WaypointEditor:

    def __init__(self, settings):
        self.logger = get_logger("editor")
        self.settings = settings
        self.handler = KeybindsInput(settings)
        self.db = DatabaseInterface(settings['PREFERENCES'].get("DB_Name", "profiles.db"))
        self.default_bases = default_bases
        self.wps_list = list()
        self.msns_list = list()
        self.aircraft = "hornet"

    def get_profile(self, profilename):
        return Profile(profilename, self.db, self.aircraft)

    def get_profile_names(self):
        return self.db.get_profile_names()

    def save_profile(self, profile):
        self.db.save_profile(profile)

    def enter_number(self, number, two_enters=False):
        self.handler.enter_number(number, two_enters)

    def enter_coords(self, latlong, elev, pp):
        self.handler.enter_coords(latlong, elev, pp)

    def enter_waypoints(self, wps, sequences):
        self.handler.enter_waypoints(wps, sequences)

    def enter_pp_msn(self, msn, n):
        self.handler.enter_pp_msn(msn, n)

    def enter_missions(self, msns):
        self.handler.enter_missions(msns)

    def enter_all(self, profile):
        sleep(int(self.settings['PREFERENCES'].get('Grace_Period', 5)))
        self.handler.enter_missions(profile.missions)
        sleep(1)
        self.handler.enter_waypoints(profile.waypoints, profile.sequences_dict)
