from dataclasses import dataclass, asdict
from typing import Any
from LatLon23 import LatLon, Longitude, Latitude
import json
import urllib.request
from os import walk, path
from src.logger import get_logger

from src.models import ProfileModel, WaypointModel, SequenceModel, IntegrityError, db


default_bases = dict()

logger = get_logger(__name__)


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
            basedict[name] = Waypoint(position=position, name=name, elevation=elev)


def generate_default_bases():
    default_bases_builder_logger = get_logger("default_bases_builder")

    pgdata = update_base_data("https://raw.githubusercontent.com/Santi871/HornetWaypointEditor/master/data/"
                              "pg.json?token=ACQW6PPI77ATCRJ2RZSDSBC44UAOG", f".\\data\\pg.json")

    caucdata = update_base_data("https://raw.githubusercontent.com/Santi871/HornetWaypointEditor/master/data/"
                                "cauc.json?token=ACQW6PIVKSD72T7FLOBQHCC44W334", f".\\data\\cauc.json")

    if pgdata and caucdata:
        default_bases_builder_logger.info("PG and Caucasus default bases updated succesfully")
    else:
        default_bases_builder_logger.warning("Failed to update PG and Caucasus default bases")

    for _, _, files in walk(".\\data"):
        for filename in files:
            if ".json" in filename:
                with open(".\\data\\" + filename, "r") as f:
                    try:
                        load_base_data(json.load(f), default_bases)
                        default_bases_builder_logger.info(
                            f"Default base data built succesfully from file: {filename}")
                    except AttributeError:
                        default_bases_builder_logger.warning(
                            f"Failed to build default base data from file: {filename}", exc_info=True)


@dataclass
class Waypoint:
    position: Any
    number: int = 0
    elevation: int = 0
    name: str = ""
    sequence: int = 0
    wp_type: str = "WP"
    latitude: float = None
    longitude: float = None

    def __post_init__(self):
        if type(self.position) == str:
            base = default_bases.get(self.position)

            if base is not None:
                self.elevation = base.elev
                self.name = self.position
                self.position = base.position
            else:
                raise ValueError("Base name not found in default bases list")

        elif not type(self.position) == LatLon:
            raise ValueError(
                "Waypoint position must be a LatLon object or base name string")

        self.latitude = self.position.lat.decimal_degree
        self.longitude = self.position.lon.decimal_degree

    def __str__(self):
        strrep = f"{self.wp_type}{self.number}"
        if self.wp_type == "WP" and self.sequence:
            strrep += f" | SEQ{self.sequence}"
        if self.name:
            strrep += f" | {self.name}"
        return strrep

    @property
    def as_dict(self):
        d = asdict(self)
        del d["position"]
        return d

    @staticmethod
    def to_object(waypoint):
        return Waypoint(
            LatLon(
                Latitude(waypoint.get('latitude')),
                Longitude(waypoint.get('longitude'))
            ),
            elevation=waypoint.get('elevation'),
            name=waypoint.get('name'),
            sequence=waypoint.get('sequence'),
            wp_type=waypoint.get('wp_type')
        )


@dataclass
class MSN(Waypoint):
    station: int = 0

    def __post_init__(self):
        super().__post_init__()
        self.wp_type = "MSN"
        if not self.station:
            raise ValueError("MSN station not defined")

    def __str__(self):
        strrep = f"MSN{self.number} | STA{self.station}"
        if self.name:
            strrep += f" | {self.name}"
        return strrep

    @staticmethod
    def to_object(waypoint):
        return MSN(
            LatLon(
                Latitude(waypoint.get('latitude')),
                Longitude(waypoint.get('longitude'))
            ),
            elevation=waypoint.get('elevation'),
            name=waypoint.get('name'),
            sequence=waypoint.get('sequence'),
            wp_type=waypoint.get('wp_type'),
            station=waypoint.get('station')
        )


class Profile:
    def __init__(self, profilename, waypoints=None, aircraft="hornet"):
        self.profilename = profilename
        self.aircraft = aircraft

        if waypoints is None:
            self.waypoints = list()
        else:
            self.waypoints = waypoints
            self.update_waypoint_numbers()

    def __str__(self):
        return json.dumps(self.to_dict())

    def update_sequences(self):
        sequences = set()
        for waypoint in self.waypoints:
            if type(waypoint) == Waypoint and waypoint.sequence:
                sequences.add(waypoint.sequence)
        sequences = list(sequences)
        sequences.sort()
        return sequences

    @property
    def has_waypoints(self):
        return len(self.waypoints) > 0

    @property
    def sequences(self):
        return self.update_sequences()

    @property
    def waypoints_as_list(self):
        return [wp for wp in self.waypoints if type(wp) == Waypoint]

    @property
    def all_waypoints_as_list(self):
        return [wp for wp in self.waypoints if not isinstance(wp, MSN)]

    @property
    def msns_as_list(self):
        return [wp for wp in self.waypoints if isinstance(wp, MSN)]

    @property
    def stations_dict(self):
        stations = dict()
        for mission in self.msns_as_list:
            station_msn_list = stations.get(mission.station, list())
            station_msn_list.append(mission)
            stations[mission.station] = station_msn_list
        return stations

    @property
    def waypoints_dict(self):
        wps_dict = dict()
        for wp in self.waypoints_as_list:
            wps_list = wps_dict.get(wp.wp_type, list())
            wps_list.append(wp)
            wps_dict[wp.wp_type] = wps_list
        return wps_dict

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

    def waypoints_of_type(self, wp_type):
        return [wp for wp in self.waypoints if wp.wp_type == wp_type]

    def get_sequence(self, identifier):
        return self.sequences_dict.get(identifier, list())

    def to_dict(self):
        return dict(
            waypoints=[waypoint.as_dict for waypoint in self.waypoints],
            name=self.profilename,
            aircraft=self.aircraft
        )

    def update_waypoint_numbers(self):
        for _, station_msn_list in self.stations_dict.items():
            for i, mission in enumerate(station_msn_list, 1):
                mission.number = i

        for _, waypoint_list in self.waypoints_dict.items():
            for i, waypoint in enumerate(waypoint_list, 1):
                waypoint.number = i

    @staticmethod
    def from_string(profile_string):
        profile_data = json.loads(profile_string)
        try:
            profile_name = profile_data["name"]
            waypoints = profile_data["waypoints"]
            wps = [Waypoint.to_object(w) for w in waypoints if w['wp_type'] != 'MSN']
            msns = [MSN.to_object(w) for w in waypoints if w['wp_type'] == 'MSN']
            aircraft = profile_data["aircraft"]
            profile = Profile(profile_name, waypoints=wps+msns, aircraft=aircraft)
            if profile.profilename:
                profile.save()
            return profile

        except Exception as e:
            logger.error(e)
            raise ValueError("Failed to load profile from data")

    def save(self, profilename=None):
        delete_list = list()
        if profilename is not None:
            self.profilename = profilename

        try:
            with db.atomic():
                profile = ProfileModel.create(
                    name=self.profilename, aircraft=self.aircraft)
        except IntegrityError:
            profile = ProfileModel.get(
                ProfileModel.name == self.profilename)
        profile.aircraft = self.aircraft

        for waypoint in profile.waypoints:
            delete_list.append(waypoint)

        for sequence in profile.sequences:
            delete_list.append(sequence)

        sequences_db_instances = dict()
        for sequencenumber in self.sequences:
            sequence_db_instance = SequenceModel.create(
                identifier=sequencenumber,
                profile=profile
            )
            sequences_db_instances[sequencenumber] = sequence_db_instance

        for waypoint in self.waypoints:
            if not isinstance(waypoint, MSN):
                sequence = sequences_db_instances.get(waypoint.sequence)
                WaypointModel.create(
                    name=waypoint.name,
                    latitude=waypoint.position.lat.decimal_degree,
                    longitude=waypoint.position.lon.decimal_degree,
                    elevation=waypoint.elevation,
                    profile=profile,
                    sequence=sequence,
                    wp_type=waypoint.wp_type
                )
            else:
                WaypointModel.create(
                    name=waypoint.name,
                    latitude=waypoint.position.lat.decimal_degree,
                    longitude=waypoint.position.lon.decimal_degree,
                    elevation=waypoint.elevation,
                    profile=profile,
                    wp_type=waypoint.wp_type,
                    station=waypoint.station
                )

        for instance in delete_list:
            instance.delete_instance()
        profile.save()

    @staticmethod
    def load(profile_name):
        profile = ProfileModel.get(ProfileModel.name == profile_name)
        aircraft = profile.aircraft

        wps = list()
        for waypoint in profile.waypoints:
            if waypoint.wp_type != "MSN":
                wp = Waypoint(LatLon(Latitude(waypoint.latitude), Longitude(waypoint.longitude)),
                              elevation=waypoint.elevation, name=waypoint.name, sequence=waypoint.sequence,
                              wp_type=waypoint.wp_type)
            else:
                wp = MSN(LatLon(Latitude(waypoint.latitude), Longitude(waypoint.longitude)),
                         elevation=waypoint.elevation, name=waypoint.name, sequence=waypoint.sequence,
                         wp_type=waypoint.wp_type, station=waypoint.station)
            wps.append(wp)

        profile = Profile(profile_name, waypoints=wps, aircraft=aircraft)
        profile.update_waypoint_numbers()
        logger.debug(
            f"Fetched {profile_name} from DB, with {len(wps)} waypoints")
        return profile

    @staticmethod
    def delete(profile_name):
        profile = ProfileModel.get(name=profile_name)

        for waypoint in profile.waypoints:
            waypoint.delete_instance()

        profile.delete_instance(recursive=True)

    @staticmethod
    def list_all():
        return list(ProfileModel.select())
