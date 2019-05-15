import keyboard
from time import sleep
from waypoints import keybinds
import logging
from objects import MSN, Wp
import configparser
import LatLon23
import sys


logging.basicConfig(format='%(levelname)s - %(message)s', level=logging.INFO)
config = configparser.ConfigParser()
active_wps = list()
active_msns = list()


def build_msns_and_wps(filename):
    config.read(filename)
    missions = config["PREPLANNED MISSIONS"]
    waypoints = config["WAYPOINTS"]

    if missions["Active_MSNs"]:
        active_missions = [int(x) for x in missions["Active_MSNs"].split(",") if x != ""]
        logging.info(f"Building {len(active_missions)} preplanned missions")

        for i in active_missions:
            msn = None
            if not missions[f"MSN{i}_LatLon"] and not missions[f"MSN{i}_MGRS"]:
                logging.warning(f"Preplanned mission {i} is set as active but target position is undefined, skipping")
                continue

            if not missions[f"MSN{i}_Elev"]:
                logging.warning(f"Preplanned mission {i} is set as active but target elevation is undefined, skipping")
                continue

            if missions[f"MSN{i}_MGRS"]:
                msn = MSN(missions[f"MSN{i}_MGRS"], int(missions[f"MSN{i}_Elev"]))

            if missions[f"MSN{i}_LatLon"]:
                if msn is not None:
                    logging.warning(f"Preplanned mission {i} had MGRS as well as LatLon defined, LatLon overwrites MGRS")

                latlon = missions[f"MSN{i}_LatLon"].split(",")
                latlon = LatLon23.string2latlon(latlon[0], latlon[1], "d% %m% %S")
                msn = MSN(latlon, int(missions[f"MSN{i}_Elev"]))

            if msn is None:
                logging.warning(f"Preplanned mission {i} is set as active but is undefined, skipping")
            else:
                active_msns.append(msn)

        logging.info(f"Built {len(active_msns)} preplanned missions")
        if len(active_msns) > 6:
            logging.warning("There are more than 6 active preplanned missions, only the first 6 will be entered")

    if waypoints["Active_WPs"]:
        active_waypoints = [int(x) for x in waypoints["Active_WPs"].split(",") if x != ""]
        logging.info(f"Building {len(active_waypoints)} waypoints")

        for i in active_waypoints:
            wpt = None

            if waypoints[f"WP{i}_MGRS"]:
                wpt = Wp(waypoints[f"WP{i}_MGRS"])

            if waypoints[f"WP{i}_LatLon"]:
                if wpt is not None:
                    logging.warning(f"Waypoint {i} had MGRS as well as LatLon defined, LatLon overwrites MGRS")

                latlon = waypoints[f"WP{i}_LatLon"].split(",")
                latlon = LatLon23.string2latlon(latlon[0], latlon[1], "d% %m% %S")
                wpt = MSN(latlon, int(waypoints[f"WP{i}_Elev"]))

            if wpt is not None and waypoints[f"WP{i}_Elev"]:
                wpt.elevation = int(waypoints[f"WP{i}_Elev"])

            if waypoints[f"WP{i}_Name"]:
                if wpt is not None:
                    logging.warning(f"Waypoint {i} had Name as well as lat/lon or MGRS defined, Name overwrites")

                wpt = Wp(waypoints[f"WP{i}_Name"])

            if wpt is None:
                logging.warning(f"Waypoint {i} is set as active but is undefined, skipping")
            else:
                active_wps.append(wpt)

        logging.info(f"Built {len(active_wps)} waypoints")


def press_with_delay(key, delay_after=0.2, delay_release=0.2):
    keyboard.press(key)
    sleep(delay_release)
    keyboard.release(key)
    sleep(delay_after)


def enter_number(number, two_enters=False):

    for num in str(number):
        if num == ".":
            break

        press_with_delay(keybinds.get(f"ufc_{num}"))

    press_with_delay(keybinds.get("ufc_enter"), delay_release=0.5)

    i = str(number).find(".")

    if i > 0 and str(number)[i+1] != "0":
        for num in str(number)[str(number).find(".")+1:]:
            press_with_delay(keybinds.get(f"ufc_{num}"))

    if two_enters:
        press_with_delay(keybinds.get("ufc_enter"), delay_release=0.5)


def enter_coords(lat, long, elev):
    press_with_delay(keybinds.get("ufc_2"), delay_release=0.5)
    enter_number(lat)
    sleep(0.5)
    press_with_delay(keybinds.get("ufc_6"), delay_release=0.5)
    enter_number(long)

    if elev:
        press_with_delay(keybinds.get("ufc_hgt"))
        press_with_delay(keybinds.get("ufc_pos"))
        press_with_delay(keybinds.get("ufc_clr"))
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

    press_with_delay(keybinds.get("ufc_pos"))
    press_with_delay(keybinds.get("ufc_2"), delay_release=0.5)
    enter_number(lat_str, two_enters=True)

    press_with_delay(keybinds.get("ufc_hgt"))
    press_with_delay(keybinds.get("ufc_6"), delay_release=0.5)
    enter_number(lon_str, two_enters=True)

    press_with_delay(keybinds.get("lddi_pb14"))
    press_with_delay(keybinds.get("lddi_pb14"))

    if elev:
        press_with_delay(keybinds.get("ufc_pb4"))
        press_with_delay(keybinds.get("ufc_pb4"))

        elev = round(float(elev)/3.2808)
        enter_number(elev)


def enter_waypoints(wps):
    i = 1
    press_with_delay(keybinds.get("hsi_data"))
    press_with_delay(keybinds.get("ufc_clr"))
    press_with_delay(keybinds.get("ufc_clr"))

    for wp in wps:

        if not wp.name:
            logging.info(f"Entering waypoint {i}: N{wp.position.lat}, E{wp.position.lon}")
        else:
            logging.info(f"Entering waypoint {i} - {wp.name}: N{wp.position.lat}, E{wp.position.lon}")

        press_with_delay(keybinds.get("hsi_arrowup"))
        press_with_delay(keybinds.get("hsi_ufc"))
        press_with_delay(keybinds.get("ufc_pos"))
        lat_str, lon_str = latlon_tostring(wp.position)

        enter_coords(lat_str, lon_str, wp.elevation)
        press_with_delay(keybinds.get("ufc_clr"))

        i += 1
        sleep(1)

    press_with_delay(keybinds.get("ufc_clr"))
    press_with_delay(keybinds.get("hsi_data"))


def enter_pp_msn(msn, n):
    logging.info(f"Entering PP mission {n} at N{msn.position.lat}, E{msn.position.lon}")

    press_with_delay(keybinds.get(f"lddi_pb{n + 5}"))
    press_with_delay(keybinds.get("lddi_pb14"))
    press_with_delay(keybinds.get("ufc_hgt"))

    enter_pp_coord(msn.position, msn.elevation)

    press_with_delay(keybinds.get("ufc_clr"))
    press_with_delay(keybinds.get("ufc_clr"))


def enter_missions(msns):

    press_with_delay(keybinds.get("lddi_pb11"))
    press_with_delay(keybinds.get("lddi_pb4"))

    n = 1
    for msn in msns:
        enter_pp_msn(msn, n)
        n += 1

    press_with_delay(keybinds.get("lddi_pb19"))
    press_with_delay(keybinds.get("lddi_pb6"))


if __name__ == "__main__":
    try:
        build_msns_and_wps(sys.argv[0])
    except IndexError:
        build_msns_and_wps("waypoints.ini")

    sleep(5)

    if len(active_wps):
        logging.info(f"Entering {len(active_wps)} waypoints")
        # enter_waypoints(active_wps[:5])

    if len(active_msns):
        logging.info(f"Entering {len(active_msns)} PP missions")
        # enter_missions(active_msns{:5)

    logging.info("Finished")
