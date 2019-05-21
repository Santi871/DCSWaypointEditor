import keyboard
from time import sleep
from configparser import ConfigParser
import LatLon23
from src.keybinds import BindsManager
from src.objects import MSN, Wp


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


class WaypointEditor:

    def __init__(self, wps_filename, settings, logger):
        self.logger = logger
        self.wps_filename = wps_filename
        self.settings = settings
        self.binds_manager = BindsManager(logger, settings)
        self.wps_list = None
        self.msns_list = None

    def build_msns_and_wps(self):
        self.wps_list = list()
        self.msns_list = list()
        config = ConfigParser()
        config.read(self.wps_filename)
        missions = config["PREPLANNED MISSIONS"]
        waypoints = config["WAYPOINTS"]

        if missions["Active_MSNs"]:
            active_missions = [int(x) for x in missions["Active_MSNs"].split(",") if x != ""]
            self.logger.info(f"Building {len(active_missions)} preplanned missions")

            for i in active_missions:
                msn = None
                if not missions[f"MSN{i}_LatLon"]:
                    self.logger.error(f"Preplanned mission {i} is set as active but target position is undefined"
                                      f" skipping")
                    continue

                if not missions[f"MSN{i}_Elev"]:
                    self.logger.error(f"Preplanned mission {i} is set as active but target elevation is undefined,"
                                      f" skipping")
                    continue

                if missions[f"MSN{i}_LatLon"]:
                    latlon = missions[f"MSN{i}_LatLon"].split("/")
                    latlon = LatLon23.string2latlon(latlon[0], latlon[1], "d% %m% %S")
                    msn = MSN(latlon, int(missions[f"MSN{i}_Elev"]), name=missions[f"MSN{i}_Name"])

                if msn is None:
                    self.logger.error(f"Preplanned mission {i} is set as active but is undefined, skipping")
                else:
                    self.msns_list .append(msn)

            self.logger.info(f"Built {len(self.msns_list )} preplanned missions")
            if len(self.msns_list ) > 6:
                self.logger.warning("There are more than 6 active preplanned missions, only the first 6 will be"
                                    " entered")

        if waypoints["Active_WPs"]:
            active_waypoints = [int(x) for x in waypoints["Active_WPs"].split(",") if x != ""]
            self.logger.info(f"Building {len(active_waypoints)} waypoints")

            for i in active_waypoints:
                wpt = None
                if not waypoints[f"WP{i}_Elev"]:
                    elev = 0
                else:
                    elev = int(waypoints[f"WP{i}_Elev"])

                if waypoints[f"WP{i}_LatLon"]:
                    latlon = waypoints[f"WP{i}_LatLon"].split("/")
                    latlon = LatLon23.string2latlon(latlon[0], latlon[1], "d% %m% %S")

                    wpt = Wp(latlon, elev)

                if wpt is not None and waypoints[f"WP{i}_Elev"]:
                    wpt.elevation = int(waypoints[f"WP{i}_Elev"])

                if waypoints[f"WP{i}_Name"]:
                    wpt = Wp(waypoints[f"WP{i}_Name"])

                if wpt is None:
                    self.logger.error(f"Waypoint {i} is set as active but is undefined, skipping")
                else:
                    self.wps_list.append(wpt)

            self.logger.info(f"Built {len(self.wps_list)} waypoints")

        return self.wps_list, self.msns_list[:5]

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
