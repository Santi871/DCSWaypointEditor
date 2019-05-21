from dataclasses import dataclass
from typing import Any
from LatLon23 import LatLon, Longitude, Latitude
import json
import urllib.request


default_bases = dict()


def update_base_data(url, filename):
    with urllib.request.urlopen(url) as response:
        html = response.read()

    with open(filename, "w+") as f2:
        f2.write(html.decode('utf-8'))


def load_base_data(basedata, basedict):
    for _, base in basedata.items():
        name = base.get('name')
        lat = base.get('locationDetails').get('lat')
        lon = base.get('locationDetails').get('lon')
        elev = round(base.get('locationDetails').get('altitude'))
        position = LatLon(Latitude(degree=lat), Longitude(degree=lon))

        basedict[name] = Base(name, position, elev)


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

            if base is not None:
                self.elevation = base.elev
                self.name = self.position
                self.position = base.position
            else:
                raise ValueError("Base name not found in default bases list")
            return

        if not type(self.position) == LatLon:
            raise ValueError("Waypoint position must be a LatLon object or base name string")


@dataclass
class MSN:
    position: LatLon
    elevation: float
    name: str = ""


update_base_data("https://raw.githubusercontent.com/Santi871/HornetWaypointEditor/master/data/"
                 "pg.json?token=ACQW6PPI77ATCRJ2RZSDSBC44UAOG", "./data/pg.json")

update_base_data("https://raw.githubusercontent.com/Santi871/HornetWaypointEditor/master/data/"
                 "cauc.json?token=ACQW6PIVKSD72T7FLOBQHCC44W334", "./data/cauc.json")

with open("./data/cauc.json", "r") as f:
    cauc_data = json.load(f)

with open("./data/pg.json", "r") as f:
    pg_data = json.load(f)

load_base_data(cauc_data, default_bases)
load_base_data(pg_data, default_bases)
