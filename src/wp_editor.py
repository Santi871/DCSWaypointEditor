import keyboard
from time import sleep
from configparser import ConfigParser
import LatLon23
from src.keybinds import BindsManager
from src.objects import MSN, Wp, default_bases
from src.db import DatabaseInterface


def press_with_delay(key, delay_after=0.2, delay_release=0.2):
    keyboard.press(key)
    sleep(delay_release)
    keyboard.release(key)
    sleep(delay_after)


def latlon_tostring(latlong):
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


class KeybindsInput:

    def __init__(self, settings, logger):
        self.logger = logger
        self.settings = settings
        self.binds_manager = BindsManager(logger, settings['PREFERENCES'])

    def enter_number(self, number, two_enters=False):
        for num in str(number):
            if num == ".":
                break

            press_with_delay(self.binds_manager.ufc(num))

        press_with_delay(self.binds_manager.ufc("ENT"), delay_release=0.5)

        i = str(number).find(".")

        if i > 0 and str(number)[i + 1] != "0":
            for num in str(number)[str(number).find(".") + 1:]:
                press_with_delay(self.binds_manager.ufc(num))

        if two_enters:
            press_with_delay(self.binds_manager.ufc("ENT"), delay_release=0.5)

    def enter_coords(self, latlong, elev, pp):
        lat_str, lon_str = latlon_tostring(latlong)

        if not pp:
            if latlong.lat.degree > 0:
                press_with_delay(self.binds_manager.ufc("2"), delay_release=0.5)
            else:
                press_with_delay(self.binds_manager.ufc("8"), delay_release=0.5)
            self.enter_number(lat_str)
            sleep(0.5)

            if latlong.lon.degree > 0:
                press_with_delay(self.binds_manager.ufc("6"), delay_release=0.5)
            else:
                press_with_delay(self.binds_manager.ufc("4"), delay_release=0.5)
            self.enter_number(lon_str)

            if elev:
                press_with_delay(self.binds_manager.ufc("OSB3"))
                press_with_delay(self.binds_manager.ufc("OSB1"))
                # press_with_delay(self.binds_manager.ufc("OSB3"))
                self.enter_number(elev)
        else:
            press_with_delay(self.binds_manager.ufc("OSB1"))
            if latlong.lat.degree > 0:
                press_with_delay(self.binds_manager.ufc("2"), delay_release=0.5)
            else:
                press_with_delay(self.binds_manager.ufc("8"), delay_release=0.5)
            self.enter_number(lat_str, two_enters=True)

            press_with_delay(self.binds_manager.ufc("OSB3"))

            if latlong.lon.degree > 0:
                press_with_delay(self.binds_manager.ufc("6"), delay_release=0.5)
            else:
                press_with_delay(self.binds_manager.ufc("4"), delay_release=0.5)

            self.enter_number(lon_str, two_enters=True)

            press_with_delay(self.binds_manager.lmdi("14"))
            press_with_delay(self.binds_manager.lmdi("14"))

            if elev:
                press_with_delay(self.binds_manager.ufc("OSB4"))
                press_with_delay(self.binds_manager.ufc("OSB4"))
                elev = round(float(elev) / 3.2808)
                self.enter_number(elev)

    def enter_waypoints(self, wps):
        i = 1
        press_with_delay(self.binds_manager.ampcd("10"))
        press_with_delay(self.binds_manager.ufc("CLR"))
        press_with_delay(self.binds_manager.ufc("CLR"))

        for wp in wps:

            if not wp.name:
                self.logger.info(f"Entering waypoint {i}")
            else:
                self.logger.info(f"Entering waypoint {i} - {wp.name}")

            press_with_delay(self.binds_manager.ampcd("12"))
            press_with_delay(self.binds_manager.ampcd("5"))
            press_with_delay(self.binds_manager.ufc("OSB1"))
            self.enter_coords(wp.position, wp.elevation, pp=False)
            press_with_delay(self.binds_manager.ufc("CLR"))

            i += 1
            sleep(1)

        press_with_delay(self.binds_manager.ufc("CLR"))
        press_with_delay(self.binds_manager.ampcd("10"))

    def enter_pp_msn(self, msn, n):
        if msn.name:
            self.logger.info(f"Entering PP mission {n} - {msn.name}")
        else:
            self.logger.info(f"Entering PP mission {n}")

        press_with_delay(self.binds_manager.lmdi(f"{n + 5}"))
        press_with_delay(self.binds_manager.lmdi("14"))
        press_with_delay(self.binds_manager.ufc("OSB3"))

        self.enter_coords(msn.position, msn.elevation, pp=True)

        press_with_delay(self.binds_manager.ufc("CLR"))
        press_with_delay(self.binds_manager.ufc("CLR"))

    def enter_missions(self, msns):

        press_with_delay(self.binds_manager.lmdi("11"))
        press_with_delay(self.binds_manager.lmdi("4"))

        n = 1
        for msn in msns:
            self.enter_pp_msn(msn, n)
            n += 1

        press_with_delay(self.binds_manager.lmdi("6"))
        press_with_delay(self.binds_manager.lmdi("19"))
        press_with_delay(self.binds_manager.lmdi("6"))


class WaypointEditor:

    def __init__(self, wps_filename, settings, logger):
        self.logger = logger
        self.wps_filename = wps_filename
        self.settings = settings
        self.handler = KeybindsInput(settings, logger)
        self.db = DatabaseInterface('profiles.db', logger)
        self.default_bases = default_bases
        self.wps_list = list()
        self.msns_list = list()

    def get_profile(self, profilename):
        missions, waypoints = self.db.get_profile(profilename)
        return missions, waypoints

    def save_profile(self, name, msns, wps):
        self.db.save_profile(name, msns, wps)

    def enter_number(self, number, two_enters=False):
        self.handler.enter_number(number, two_enters)

    def enter_coords(self, latlong, elev, pp):
        self.handler.enter_coords(latlong, elev, pp)

    def enter_waypoints(self, wps):
        self.handler.enter_waypoints(wps)

    def enter_pp_msn(self, msn, n):
        self.handler.enter_pp_msn(msn, n)

    def enter_missions(self, msns):
        self.handler.enter_missions(msns)

    def enter_all(self, msns, wps):
        sleep(self.settings['PREFERENCES'].get('Grace_Period', 5))
        self.handler.enter_missions(msns)
        sleep(1)
        self.handler.enter_waypoints(wps)
