import socket
from time import sleep
from configparser import NoOptionError


class DriverException(Exception):
    pass


def latlon_tostring(latlong, decimal_minutes_mode=False, easting_zfill=2):

    if not decimal_minutes_mode:
        lat_deg = str(abs(round(latlong.lat.degree)))
        lat_min = str(abs(round(latlong.lat.minute))).zfill(2)
        lat_sec = abs(latlong.lat.second)

        lat_sec_int, lat_sec_dec = divmod(lat_sec, 1)

        lat_sec = str(int(lat_sec_int)).zfill(2)

        if lat_sec_dec:
            lat_sec += "." + str(round(lat_sec_dec, 2))[2:4]

        lon_deg = str(abs(round(latlong.lon.degree))).zfill(easting_zfill)
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

        lon_deg = str(abs(round(latlong.lon.degree))).zfill(easting_zfill)
        lon_min = str(round(latlong.lon.decimal_minute, 4))

        lon_min_split = lon_min.split(".")
        lon_min_split[0] = lon_min_split[0].zfill(2)
        lon_min = ".".join(lon_min_split)

        return lat_deg + lat_min, lon_deg + lon_min


class Driver:
    def __init__(self, logger, config, host="127.0.0.1", port=7778):
        self.logger = logger
        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.host, self.port = host, port
        self.config = config
        self.limits = dict()

        try:
            self.short_delay = float(self.config.get("PREFERENCES", "button_release_short_delay"))
            self.medium_delay = float(self.config.get("PREFERENCES", "button_release_medium_delay"))
        except NoOptionError:
            self.short_delay, self.medium_delay = 0.2, 0.5

    def press_with_delay(self, key, delay_after=None, delay_release=None):
        if not key:
            return

        if delay_after is None:
            delay_after = self.short_delay

        if delay_release is None:
            delay_release = self.short_delay

        # TODO get rid of the OSB -> OS replacement
        self.s.sendto(f"{key} 1\n".replace("OSB", "OS").encode(
            "utf-8"), (self.host, self.port))
        sleep(delay_release)

        self.s.sendto(f"{key} 0\n".replace("OSB", "OS").encode(
            "utf-8"), (self.host, self.port))
        sleep(delay_after)

    def validate_waypoint(self, waypoint):
        try:
            return self.limits[waypoint.wp_type] is None or waypoint.number <= self.limits[waypoint.wp_type]
        except KeyError:
            return False

    def validate_waypoints(self, waypoints):
        for waypoint in waypoints:
            if not self.validate_waypoint(waypoint):
                waypoints.remove(waypoint)
        return waypoints

    def stop(self):
        self.s.close()


class HornetDriver(Driver):
    def __init__(self, logger, config):
        super().__init__(logger, config)
        self.limits = dict(WP=None, MSN=6)

    def ufc(self, num, delay_after=None, delay_release=None):
        key = f"UFC_{num}"
        self.press_with_delay(key, delay_after=delay_after,
                              delay_release=delay_release)

    def lmdi(self, pb, delay_after=None, delay_release=None):
        key = f"LEFT_DDI_PB_{pb.zfill(2)}"
        self.press_with_delay(key, delay_after=delay_after,
                              delay_release=delay_release)

    def ampcd(self, pb, delay_after=None, delay_release=None):
        key = f"AMPCD_PB_{pb.zfill(2)}"
        self.press_with_delay(key, delay_after=delay_after,
                              delay_release=delay_release)

    def enter_number(self, number, two_enters=False):
        for num in str(number):
            if num == ".":
                break

            self.ufc(num)

        self.ufc("ENT", delay_release=self.medium_delay)

        i = str(number).find(".")

        if two_enters:
            if i > 0:
                for num in str(number)[str(number).find(".") + 1:]:
                    self.ufc(num)

            self.ufc("ENT", delay_release=self.medium_delay)

    def enter_coords(self, latlong, elev, pp, decimal_minutes_mode=False):
        lat_str, lon_str = latlon_tostring(latlong, decimal_minutes_mode=decimal_minutes_mode)
        self.logger.debug(f"Entering coords string: {lat_str}, {lon_str}")

        if not pp:
            if latlong.lat.degree > 0:
                self.ufc("2", delay_release=self.medium_delay)
            else:
                self.ufc("8", delay_release=self.medium_delay)
            self.enter_number(lat_str, two_enters=True)
            sleep(0.5)

            if latlong.lon.degree > 0:
                self.ufc("6", delay_release=self.medium_delay)
            else:
                self.ufc("4", delay_release=self.medium_delay)
            self.enter_number(lon_str, two_enters=True)

            if elev:
                self.ufc("OSB3")
                self.ufc("OSB1")
                self.enter_number(elev)
        else:
            self.ufc("OSB1")
            if latlong.lat.degree > 0:
                self.ufc("2", delay_release=self.medium_delay)
            else:
                self.ufc("8", delay_release=self.medium_delay)
            self.enter_number(lat_str, two_enters=True)

            self.ufc("OSB3")

            if latlong.lon.degree > 0:
                self.ufc("6", delay_release=self.medium_delay)
            else:
                self.ufc("4", delay_release=self.medium_delay)

            self.enter_number(lon_str, two_enters=True)

            self.lmdi("14")
            self.lmdi("14")

            if elev:
                self.ufc("OSB4")
                self.ufc("OSB4")
                elev = round(float(elev) / 3.2808)
                self.enter_number(elev)

    def enter_waypoints(self, wps, sequences):
        if not wps:
            return

        self.ampcd("10")
        self.ampcd("19")
        self.ufc("CLR")
        self.ufc("CLR")

        for i, wp in enumerate(wps):
            if not wp.name:
                self.logger.info(f"Entering waypoint {i+1}")
            else:
                self.logger.info(f"Entering waypoint {i+1} - {wp.name}")

            self.ampcd("12")
            self.ampcd("5")
            self.ufc("OSB1")
            self.enter_coords(wp.position, wp.elevation, pp=False, decimal_minutes_mode=True)
            self.ufc("CLR")

        for sequencenumber, waypointslist in sequences.items():
            if sequencenumber != 1:
                self.ampcd("15")
                self.ampcd("15")
            else:
                waypointslist = [0] + waypointslist

            self.ampcd("1")

            for waypoint in waypointslist:
                self.ufc("OSB4")
                self.enter_number(waypoint)

        self.ufc("CLR")
        self.ufc("CLR")
        self.ufc("CLR")
        self.ampcd("19")
        self.ampcd("10")

    def enter_pp_msn(self, msn, n):
        if msn.name:
            self.logger.info(f"Entering PP mission {n} - {msn.name}")
        else:
            self.logger.info(f"Entering PP mission {n}")

        self.lmdi(f"{n + 5}")
        self.lmdi("14")
        self.ufc("OSB3")

        self.enter_coords(msn.position, msn.elevation, pp=True)

        self.ufc("CLR")
        self.ufc("CLR")

    def enter_missions(self, missions):
        def stations_order(x):
            if x == 8:
                return 0
            elif x == 2:
                return 1
            elif x == 7:
                return 2
            elif x == 3:
                return 3

        sorted_stations = list()
        stations = dict()
        for mission in missions:
            station_msn_list = stations.get(mission.station, list())
            station_msn_list.append(mission)
            stations[mission.station] = station_msn_list

        for k in sorted(stations, key=stations_order):
            sorted_stations.append(stations[k])

        for msns in sorted_stations:
            msns = msns[:6]
            if not msns:
                return

            n = 1
            for msn in msns:
                self.enter_pp_msn(msn, n)
                n += 1

            self.lmdi("13")
        self.lmdi("6")

    def enter_all(self, profile):
        self.enter_missions(self.validate_waypoints(profile.msns_as_list))
        sleep(1)
        self.enter_waypoints(self.validate_waypoints(profile.waypoints_as_list), profile.sequences_dict)


class HarrierDriver(Driver):
    def __init__(self, logger, config):
        super().__init__(logger, config)
        self.limits = dict(WP=None)

    def ufc(self, num, delay_after=None, delay_release=None):
        if num not in ("ENT", "CLR"):
            key = f"UFC_B{num}"
        elif num == "ENT":
            key = "UFC_ENTER"
        elif num == "CLR":
            key = "UFC_CLEAR"
        else:
            key = f"UFC_{num}"
        self.press_with_delay(key, delay_after=delay_after,
                              delay_release=delay_release)

    def odu(self, num, delay_after=None, delay_release=None):
        key = f"ODU_OPT{num}"
        self.press_with_delay(key, delay_after=delay_after,
                              delay_release=delay_release)

    def lmpcd(self, pb, delay_after=None, delay_release=None):
        key = f"MPCD_L_{pb}"
        self.press_with_delay(key, delay_after=delay_after, delay_release=delay_release)

    def enter_number(self, number, two_enters=False):
        for num in str(number):
            if num == ".":
                break

            self.ufc(num)

        self.ufc("ENT", delay_release=self.medium_delay)

        i = str(number).find(".")

        if two_enters:
            if i > 0:
                for num in str(number)[str(number).find(".") + 1:]:
                    self.ufc(num)

            self.ufc("ENT", delay_release=self.medium_delay)

    def enter_coords(self, latlong, elev):
        lat_str, lon_str = latlon_tostring(latlong, decimal_minutes_mode=False, easting_zfill=3)
        self.logger.debug(f"Entering coords string: {lat_str}, {lon_str}")

        if latlong.lat.degree > 0:
            self.ufc("2", delay_release=self.medium_delay)
        else:
            self.ufc("8", delay_release=self.medium_delay)
        self.enter_number(lat_str)

        self.odu("2")

        if latlong.lon.degree > 0:
            self.ufc("6", delay_release=self.medium_delay)
        else:
            self.ufc("4", delay_release=self.medium_delay)

        self.enter_number(lon_str)

        self.odu("2")

        if elev:
            self.odu("3")
            self.enter_number(elev)

    def enter_waypoints(self, wps):
        self.lmpcd("2")

        for wp in wps:
            self.ufc("7")
            self.ufc("7")
            self.ufc("ENT")
            self.odu("2")
            self.enter_coords(wp.position, wp.elevation)
            self.odu("1")

        self.lmpcd("2")

    def enter_all(self, profile):
        self.enter_waypoints(self.validate_waypoints(profile.waypoints_as_list))


class MirageDriver(Driver):
    def __init__(self, logger, config):
        super().__init__(logger, config)
        self.limits = dict(WP=9)

    def pcn(self, num, delay_after=None, delay_release=None):
        if num in ("ENTER", "CLR"):
            key = f"INS_{num}_BTN"
        elif num == "PREP":
            key = "INS_PREP_SW"
        else:
            key = f"INS_BTN_{num}"

        self.press_with_delay(key, delay_after=delay_after, delay_release=delay_release)

    def enter_number(self, number):
        for num in str(number):
            if num == ".":
                continue

            self.pcn(num)
        self.pcn("ENTER")

    def enter_coords(self, latlong):
        lat_str, lon_str = latlon_tostring(latlong, decimal_minutes_mode=True, easting_zfill=3)
        self.logger.debug(f"Entering coords string: {lat_str[:-2]}, {lon_str[:-2]}")

        self.pcn("1")
        if latlong.lat.degree > 0:
            self.pcn("2", delay_release=self.medium_delay)
        else:
            self.pcn("8", delay_release=self.medium_delay)
        self.enter_number(lat_str[:-2])

        self.pcn("3")

        if latlong.lon.degree > 0:
            self.pcn("6", delay_release=self.medium_delay)
        else:
            self.pcn("4", delay_release=self.medium_delay)
        self.enter_number(lon_str[:-2])

    def enter_waypoints(self, wps):
        for i, wp in enumerate(wps, 1):
            self.pcn("PREP")
            self.pcn("0")
            self.pcn(str(i))
            self.enter_coords(wp.position)
            self.pcn("ENTER")

    def enter_all(self, profile):
        self.enter_waypoints(self.validate_waypoints(profile.waypoints_as_list))
