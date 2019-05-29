from dataclasses import dataclass
from typing import Any
from LatLon23 import LatLon, Longitude, Latitude
import json
import urllib.request


default_bases = dict()


def create_base_data(url, filename):
    with urllib.request.urlopen(url) as response:
        html = response.read()

    with open(filename, "w+") as f2:
        f2.write(html.decode('utf-8'))


def load_base_data(basedata, basedict):
    for _, base in basedata.items():
        name = base.get('name')

        if name not in ("Stennis", "Kuznetsov", "Kuznetsov North", "Kuznetsov South"):
            lat = base.get('locationDetails').get('lat')
            lon = base.get('locationDetails').get('lon')
            elev = round(base.get('locationDetails').get('altitude'))
            position = LatLon(Latitude(degree=lat), Longitude(degree=lon))
            basedict[name] = Wp(position=position, name=name, elevation=elev)


@dataclass
class Wp:
    position: Any
    elevation: float = 0
    name: str = ""
    sequence: int = 0

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
            raise ValueError("Waypoint position must be a LatLon object or base name string")

    def to_dict(self):
        d = dict(
            latitude=self.position.lat.decimal_degree,
            longitude=self.position.lon.decimal_degree,
            elevation=self.elevation,
            name=self.name,
            sequence=self.sequence
        )
        return d


@dataclass
class MSN:
    position: LatLon
    elevation: float
    name: str = ""

    def to_dict(self):
        d = dict(
            latitude=self.position.lat.decimal_degree,
            longitude=self.position.lon.decimal_degree,
            elevation=self.elevation,
            name=self.name
        )
        return d


class Profile:
    def __init__(self, profilename, db_interface, aircraft=None):
        self.profilename = profilename
        self.db_interface = db_interface
        self.aircraft = aircraft

        if profilename:
            self.missions, self.waypoints = self.db_interface.get_profile(profilename)
        else:
            self.missions, self.waypoints = list(), list()

    def update_sequences(self):
        sequences = set()
        for waypoint in self.waypoints:
            if waypoint.sequence:
                sequences.add(waypoint.sequence)
        sequences = list(sequences)
        sequences.sort()
        return sequences

    def save(self, profilename=None):
        if not self.waypoints and not self.missions:
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
    def sequences_dict(self):
        d = dict()
        for sequence_identifier in self.sequences:
            for i, wp in enumerate(self.waypoints):
                if wp.sequence == sequence_identifier:
                    wp_list = d.get(sequence_identifier, list())
                    wp_list.append(i+1)
                    d[sequence_identifier] = wp_list

        return d

    def get_sequence(self, identifier):
        return self.sequences_dict.get(identifier, list())


create_base_data("https://raw.githubusercontent.com/Santi871/HornetWaypointEditor/master/data/"
                 "pg.json?token=ACQW6PPI77ATCRJ2RZSDSBC44UAOG", "./data/pg.json")

create_base_data("https://raw.githubusercontent.com/Santi871/HornetWaypointEditor/master/data/"
                 "cauc.json?token=ACQW6PIVKSD72T7FLOBQHCC44W334", "./data/cauc.json")

with open("./data/cauc.json", "r") as f:
    cauc_data = json.load(f)

with open("./data/pg.json", "r") as f:
    pg_data = json.load(f)

load_base_data(cauc_data, default_bases)
load_base_data(pg_data, default_bases)
