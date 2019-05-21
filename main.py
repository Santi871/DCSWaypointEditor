import keyboard
from time import sleep
from configparser import ConfigParser
import LatLon23
import sys
from src.logger import logger
from src.keybinds import BindsManager
from src.objects import MSN, Wp


settings = ConfigParser()
settings.read("settings.ini")
preferences = settings['PREFERENCES']
binds_manager = BindsManager(logger, settings)


def build_msns_and_wps(filename):
    wps_list = list()
    msns_list = list()
    config = ConfigParser()
    config.read(filename)
    missions = config["PREPLANNED MISSIONS"]
    waypoints = config["WAYPOINTS"]

    if missions["Active_MSNs"]:
        active_missions = [int(x) for x in missions["Active_MSNs"].split(",") if x != ""]
        logger.info(f"Building {len(active_missions)} preplanned missions")

        for i in active_missions:
            msn = None
            if not missions[f"MSN{i}_LatLon"]:
                logger.error(f"Preplanned mission {i} is set as active but target position is undefined, skipping")
                continue

            if not missions[f"MSN{i}_Elev"]:
                logger.error(f"Preplanned mission {i} is set as active but target elevation is undefined, skipping")
                continue

            if missions[f"MSN{i}_LatLon"]:
                latlon = missions[f"MSN{i}_LatLon"].split("/")
                latlon = LatLon23.string2latlon(latlon[0], latlon[1], "d% %m% %S")
                msn = MSN(latlon, int(missions[f"MSN{i}_Elev"]), name=missions[f"MSN{i}_Name"])

            if msn is None:
                logger.error(f"Preplanned mission {i} is set as active but is undefined, skipping")
            else:
                msns_list.append(msn)

        logger.info(f"Built {len(msns_list)} preplanned missions")
        if len(msns_list) > 6:
            logger.warning("There are more than 6 active preplanned missions, only the first 6 will be entered")

    if waypoints["Active_WPs"]:
        active_waypoints = [int(x) for x in waypoints["Active_WPs"].split(",") if x != ""]
        logger.info(f"Building {len(active_waypoints)} waypoints")

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
                logger.error(f"Waypoint {i} is set as active but is undefined, skipping")
            else:
                wps_list.append(wpt)

        logger.info(f"Built {len(wps_list)} waypoints")

    return wps_list, msns_list


def press_with_delay(key, delay_after=0.2, delay_release=0.2):
    keyboard.press(key)
    sleep(delay_release)
    keyboard.release(key)
    sleep(delay_after)


def enter_number(number, two_enters=False):
    for num in str(number):
        if num == ".":
            break

        press_with_delay(binds_manager.ufc(num))

    press_with_delay(binds_manager.ufc("ENT"), delay_release=0.5)

    i = str(number).find(".")

    if i > 0 and str(number)[i+1] != "0":
        for num in str(number)[str(number).find(".")+1:]:
            press_with_delay(binds_manager.ufc(num))

    if two_enters:
        press_with_delay(binds_manager.ufc("ENT"), delay_release=0.5)


def enter_coords(lat, long, elev):
    press_with_delay(binds_manager.ufc("2"), delay_release=0.5)
    enter_number(lat)
    sleep(0.5)
    press_with_delay(binds_manager.ufc("6"), delay_release=0.5)
    enter_number(long)

    if elev:
        press_with_delay(binds_manager.ufc("OSB3"))
        press_with_delay(binds_manager.ufc("OSB1"))
        press_with_delay(binds_manager.ufc("OSB3"))
        enter_number(elev)


def latlon_tostring(latlong):
    lat_deg = str(round(latlong.lat.degree))
    lat_min = str(round(latlong.lat.minute)).zfill(2)
    lat_sec = latlong.lat.second

    lat_sec_int, lat_sec_dec = divmod(lat_sec, 1)

    lat_sec = str(int(lat_sec_int)).zfill(2)

    if lat_sec_dec:
        lat_sec += "." + str(round(lat_sec_dec, 2))[2:4]

    lon_deg = str(round(latlong.lon.degree))
    lon_min = str(round(latlong.lon.minute)).zfill(2)
    lon_sec = latlong.lon.second

    lon_sec_int, lon_sec_dec = divmod(lon_sec, 1)

    lon_sec = str(int(lon_sec_int)).zfill(2)

    if lon_sec_dec:
        lon_sec += "." + str(round(lon_sec_dec, 2))[2:4]

    return lat_deg + lat_min + lat_sec, lon_deg + lon_min + lon_sec


def enter_pp_coord(latlong, elev):
    lat_str, lon_str = latlon_tostring(latlong)

    press_with_delay(binds_manager.ufc("OSB1"))
    press_with_delay(binds_manager.ufc("2"), delay_release=0.5)
    enter_number(lat_str, two_enters=True)

    press_with_delay(binds_manager.ufc("OSB3"))
    press_with_delay(binds_manager.ufc("6"), delay_release=0.5)
    enter_number(lon_str, two_enters=True)

    press_with_delay(binds_manager.lmdi("14"))
    press_with_delay(binds_manager.lmdi("14"))

    if elev:
        press_with_delay(binds_manager.ufc("OSB4"))
        press_with_delay(binds_manager.ufc("OSB4"))

        elev = round(float(elev)/3.2808)
        enter_number(elev)


def enter_waypoints(wps):
    i = 1
    press_with_delay(binds_manager.ampcd("5"))
    press_with_delay(binds_manager.ufc("CLR"))
    press_with_delay(binds_manager.ufc("CLR"))

    for wp in wps:

        if not wp.name:
            logger.info(f"Entering waypoint {i}")
        else:
            logger.info(f"Entering waypoint {i} - {wp.name}")

        press_with_delay(binds_manager.ampcd("12"))
        press_with_delay(binds_manager.ampcd("5"))
        press_with_delay(binds_manager.ufc("OSB1"))
        lat_str, lon_str = latlon_tostring(wp.position)

        enter_coords(lat_str, lon_str, wp.elevation)
        press_with_delay(binds_manager.ufc("CLR"))

        i += 1
        sleep(1)

    press_with_delay(binds_manager.ufc("CLR"))
    press_with_delay(binds_manager.ampcd("10"))


def enter_pp_msn(msn, n):
    if msn.name:
        logger.info(f"Entering PP mission {n} - {msn.name}")
    else:
        logger.info(f"Entering PP mission {n}")

    press_with_delay(binds_manager.lmdi(f"{n + 5}"))
    press_with_delay(binds_manager.lmdi("14"))
    press_with_delay(binds_manager.ufc("OSB3"))

    enter_pp_coord(msn.position, msn.elevation)

    press_with_delay(binds_manager.ufc("CLR"))
    press_with_delay(binds_manager.ufc("CLR"))


def enter_missions(msns):

    press_with_delay(binds_manager.lmdi("11"))
    press_with_delay(binds_manager.lmdi("4"))

    n = 1
    for msn in msns:
        enter_pp_msn(msn, n)
        n += 1

    press_with_delay(binds_manager.lmdi("6"))
    press_with_delay(binds_manager.lmdi("19"))
    press_with_delay(binds_manager.lmdi("6"))


def main():
    try:
        active_wps, active_msns = build_msns_and_wps(sys.argv[1])
    except IndexError:
        active_wps, active_msns = build_msns_and_wps("waypoints.ini")

    for i in reversed(range(preferences.getint('Grace_Period', 5))):
        logger.info(f"Entering data in {i+1}...")
        sleep(1)

    if active_wps:
        logger.info(f"Entering {len(active_wps)} waypoints")
        enter_waypoints(active_wps)

    sleep(1)

    if active_msns:
        logger.info(f"Entering {len(active_msns)} PP missions")
        enter_missions(active_msns[:5])


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error("Exception occurred", exc_info=True)
        raise e

    logger.info("Finished")
