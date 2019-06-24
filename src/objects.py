from dataclasses import dataclass
from typing import Any
from LatLon23 import LatLon, Longitude, Latitude
import json
import urllib.request
from os import walk, path
from src.logger import get_logger


default_bases = dict()


def update_base_data(url, file):
    with urllib.request.urlopen(url) as response:
        if response.code == 200:
            html = response.read()
        else:
            return False

    if path.isfile(file):
        with open(file, "w") as f2:
            f2.write(html.decode('utf-8'))
    return True


def load_base_data(basedata, basedict):
    waypoints_list = basedata.get("waypoints")

    if type(waypoints_list) == list:
        basedata = {i: wp for i, wp in enumerate(waypoints_list)}

    for _, base in basedata.items():
        name = base.get('name')

        if name not in ("Stennis", "Kuznetsov", "Kuznetsov North", "Kuznetsov South"):
            lat = base.get("latitude") or base.get(
                'locationDetails').get('lat')
            lon = base.get("longitude") or base.get(
                'locationDetails').get('lon')
            elev = base.get("elevation")
            if elev is None:
                elev = base.get('locationDetails').get('altitude')
            position = LatLon(Latitude(degree=lat), Longitude(degree=lon))
            basedict[name] = Wp(position=position, name=name, elevation=elev)


def generate_default_bases():
    logger = get_logger("default_bases_builder")

    pgdata = update_base_data("https://raw.githubusercontent.com/Santi871/HornetWaypointEditor/master/data/"
                              "pg.json?token=ACQW6PPI77ATCRJ2RZSDSBC44UAOG", f".\\data\\pg.json")

    caucdata = update_base_data("https://raw.githubusercontent.com/Santi871/HornetWaypointEditor/master/data/"
                                "cauc.json?token=ACQW6PIVKSD72T7FLOBQHCC44W334", f".\\data\\cauc.json")

    if pgdata and caucdata:
        logger.info("PG and Caucasus default bases updated succesfully")
    else:
        logger.warning("Failed to update PG and Caucasus default bases")

    for _, _, files in walk(".\\data"):
        for filename in files:
            if ".json" in filename:
                with open(".\\data\\" + filename, "r") as f:
                    try:
                        load_base_data(json.load(f), default_bases)
                        logger.info(
                            f"Default base data built succesfully from file: {filename}")
                    except AttributeError:
                        logger.warning(
                            f"Failed to build default base data from file: {filename}", exc_info=True)


@dataclass
class Wp:
    position: Any
    elevation: int = 0
    name: str = ""
    sequence: int = 0
    wp_type: str = "WP"
    station: int = 0

    def __post_init__(self):
        if type(self.position) == str:
            base = default_bases.get(self.position)

            if base is not None:
                self.elevation = base.elev
                self.name = self.position
                self.position = base.position
            else:
                raise ValueError("Base name not found in default bases list")
            return

        if not type(self.position) == LatLon:
            raise ValueError(
                "Waypoint position must be a LatLon object or base name string")

        if self.wp_type == "MSN" and not self.station:
            raise ValueError("No station defined for PP MSN")

    def to_dict(self):
        return dict(
            latitude=self.position.lat.decimal_degree,
            longitude=self.position.lon.decimal_degree,
            elevation=self.elevation,
            name=self.name,
            sequence=self.sequence,
            wp_type=self.wp_type,
            station=self.station
        )


class Profile:
    def __init__(self, profilename, db_interface, waypoints=None, aircraft="hornet"):
        self.profilename = profilename
        self.db_interface = db_interface

        if profilename:
            self.waypoints, self.aircraft = self.db_interface.get_profile(
                profilename)
        else:
            self.waypoints, self.aircraft = dict(), "hornet"

    def update_sequences(self):
        sequences = set()
        for waypoint in self.waypoints.get("WP", list()):
            if waypoint.sequence:
                sequences.add(waypoint.sequence)
        sequences = list(sequences)
        sequences.sort()
        return sequences

    def save(self, profilename=None):
        if not self.waypoints:
            return

        if profilename is not None:
            self.profilename = profilename

        if profilename:
            self.db_interface.save_profile(self)
            self.profilename = profilename

    def delete(self):
        self.db_interface.delete_profile(self.profilename)

    @property
    def sequences(self):
        return self.update_sequences()

    @property
    def waypoints_as_list(self):
        wps = list()
        for wp_type, wp_list in self.waypoints.items():
            if wp_type != "MSN":
                for wp in wp_list:
                    wps.append(wp)
        return wps

    @property
    def msns_as_list(self):
        msns = list()
        stations = self.waypoints.get("MSN", dict())
        for station, msn_list in stations.items():
            for msn in msn_list:
                wp = Wp(position=msn.position, elevation=msn.elevation, name=msn.name, station=station,
                        wp_type="MSN")
                msns.append(wp)
        return msns

    @property
    def sequences_dict(self):
        d = dict()
        for sequence_identifier in self.sequences:
            for i, wp in enumerate(self.waypoints_as_list):
                if wp.sequence == sequence_identifier:
                    wp_list = d.get(sequence_identifier, list())
                    wp_list.append(i+1)
                    d[sequence_identifier] = wp_list

        return d

    def get_sequence(self, identifier):
        return self.sequences_dict.get(identifier, list())

    def to_dict(self):
        return dict(
            waypoints=[waypoint.to_dict(
            ) for waypoint in self.profile.waypoints_as_list + self.profile.msns_as_list],
            name=self.profile.profilename,
            aircraft=self.profile.aircraft
        )

    @staticmethod
    def to_object(profile_data):
        return Profile()
