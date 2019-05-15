from dataclasses import dataclass
from typing import Any
from LatLon23 import LatLon, Longitude, Latitude
import mgrs
import json


m = mgrs.MGRS()
default_bases = dict()


def load_base_data(basedata, basedict):

    for _, base in basedata.items():
        name = base.get('name')
        lat = base.get('locationDetails').get('lat')
        lon = base.get('locationDetails').get('lon')
        elev = round(base.get('locationDetails').get('altitude'))
        position = LatLon(Latitude(degree=lat), Longitude(degree=lon))

        basedict[name] = Base(name, position, elev)


@dataclass
class Coord:
    lat: int
    long: int
    elev: int = 0


@dataclass
class Base:
    name: str
    position: LatLon
    elev: int


@dataclass
class Wp:
    position: Any
    elevation: int = 0
    name: str = ""

    def __post_init__(self):
        if type(self.position) == str:
            base = default_bases.get(self.position)

            if base is None:
                latlon = m.toLatLon(self.position.encode())
                self.position = LatLon(lat=latlon[0], lon=latlon[1])
            else:
                self.elevation = base.elev
                self.name = self.position
                self.position = base.position

            return

        if not type(self.position) == LatLon:
            raise ValueError("Waypoint position must be a LatLon object or string of base name")


@dataclass
class MSN:
    position: Any
    elevation: float
    name: str = ""

    def __post_init__(self):
        if type(self.position) == str:
            latlon = m.toLatLon(self.position.encode())

            self.position = LatLon(lat=latlon[0], lon=latlon[1])
            return

        if not type(self.position) == LatLon:
            raise ValueError("Waypoint position must be a LatLon object or MGRS coordinate string")


with open("cauc.json", "r") as f:
    cauc_data = json.load(f)

with open("pg.json", "r") as f:
    pg_data = json.load(f)

load_base_data(cauc_data, default_bases)
load_base_data(pg_data, default_bases)
