from src.models import ProfileModel, WaypointModel, SequenceModel, db
from src.objects import Wp
from src.logger import get_logger
from LatLon23 import LatLon, Latitude, Longitude


class DatabaseInterface:
    def __init__(self, db_name):
        self.logger = get_logger("db")
        db.init(db_name)
        db.connect()
        db.create_tables([ProfileModel, WaypointModel, SequenceModel])
        self.logger.debug("Connected to database")

    def get_profile(self, profilename):
        profile = ProfileModel.get(ProfileModel.name == profilename)
        aircraft = profile.aircraft

        wps = dict()
        for waypoint in profile.waypoints:
            if waypoint.wp_type == "MSN":
                wps_list = wps.get(waypoint.wp_type, dict()).get(waypoint.station, list())
            else:
                wps_list = wps.get(waypoint.wp_type, list())

            if waypoint.sequence:
                sequence = waypoint.sequence.identifier
            else:
                sequence = None

            wp = Wp(LatLon(Latitude(waypoint.latitude), Longitude(waypoint.longitude)),
                    elevation=waypoint.elevation, name=waypoint.name, sequence=sequence,
                    wp_type=waypoint.wp_type, station=waypoint.station)

            if waypoint.wp_type == "MSN":
                stations = wps.get("MSN", dict())
                station = stations.get(waypoint.station, list())
                station.append(wp)
                stations[waypoint.station] = station
                wps["MSN"] = stations
            else:
                wps_list.append(wp)
                wps[waypoint.wp_type] = wps_list

        self.logger.debug(f"Fetched {profilename} from DB, with {len(wps)} waypoints")
        return wps, aircraft

    def save_profile(self, profileinstance):
        delete_list = list()
        sequences_db_instances = dict()

        profile, _ = ProfileModel.get_or_create(name=profileinstance.profilename, aircraft=profileinstance.aircraft)

        for waypoint in profile.waypoints:
            delete_list.append(waypoint)

        for sequence in profile.sequences:
            delete_list.append(sequence)

        self.logger.debug(f"Attempting to save profile {profileinstance.profilename}")
        for sequencenumber in profileinstance.sequences:
            sequence_db_instance = SequenceModel.create(identifier=sequencenumber, profile=profile)
            sequences_db_instances[sequencenumber] = sequence_db_instance

        for wp_type, wp_list in profileinstance.waypoints.items():
            if wp_type != "MSN":
                for waypoint in wp_list:
                    sequence = sequences_db_instances.get(waypoint.sequence)
                    WaypointModel.create(name=waypoint.name,
                                         latitude=waypoint.position.lat.decimal_degree,
                                         longitude=waypoint.position.lon.decimal_degree,
                                         elevation=waypoint.elevation,
                                         profile=profile,
                                         sequence=sequence,
                                         wp_type=waypoint.wp_type)
            else:
                for station, station_wps in wp_list.items():
                    for waypoint in station_wps:
                        WaypointModel.create(name=waypoint.name,
                                             latitude=waypoint.position.lat.decimal_degree,
                                             longitude=waypoint.position.lon.decimal_degree,
                                             elevation=waypoint.elevation,
                                             profile=profile,
                                             wp_type=waypoint.wp_type,
                                             station=station)

        for instance in delete_list:
            instance.delete_instance()
        profile.save()

    @staticmethod
    def delete_profile(profilename):
        profile = ProfileModel.get(name=profilename)

        for waypoint in profile.waypoints:
            waypoint.delete_instance()

        profile.delete_instance(recursive=True)

    @staticmethod
    def get_profile_names():
        return [profile.name for profile in ProfileModel.select()]

    @staticmethod
    def close():
        db.close()
