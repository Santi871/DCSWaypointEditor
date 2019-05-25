from src.models import ProfileModel, MissionModel, WaypointModel, SequenceModel, db
from src.objects import MSN, Wp
from src.logger import get_logger
from LatLon23 import LatLon, Latitude, Longitude


class DatabaseInterface:
    def __init__(self, db_name):
        self.logger = get_logger("db")
        db.init(db_name)
        db.connect()
        db.create_tables([ProfileModel, MissionModel, WaypointModel, SequenceModel])
        self.logger.debug("Connected to database")

    def get_profile(self, profilename):
        profile = ProfileModel.get(ProfileModel.name == profilename)
        msns = [MSN(LatLon(Latitude(mission.latitude), Longitude(mission.longitude)),
                    elevation=mission.elevation, name=mission.name) for mission in profile.missions]

        wps = list()
        for waypoint in profile.waypoints:
            if waypoint.sequence:
                sequence = waypoint.sequence.identifier
            else:
                sequence = None

            wp = Wp(LatLon(Latitude(waypoint.latitude), Longitude(waypoint.longitude)),
                    elevation=waypoint.elevation, name=waypoint.name, sequence=sequence)

            wps.append(wp)

        self.logger.debug(f"Fetched {profilename} from DB, with {len(msns)} missions and {len(wps)} waypoints")
        return msns, wps

    def save_profile(self, profileinstance):
        delete_list = list()
        sequences_db_instances = dict()

        profile, _ = ProfileModel.get_or_create(name=profileinstance.profilename, aircraft=profileinstance.aircraft)
        for mission in profile.missions:
            delete_list.append(mission)

        for waypoint in profile.waypoints:
            delete_list.append(waypoint)

        for sequence in profile.sequences:
            delete_list.append(sequence)

        self.logger.debug(f"Attempting to save profile {profileinstance.profilename}")
        for sequencenumber in profileinstance.sequences:
            sequence_db_instance = SequenceModel.create(identifier=sequencenumber, profile=profile)
            sequences_db_instances[sequencenumber] = sequence_db_instance

        for mission in profileinstance.missions:
            MissionModel.create(name=mission.name,
                                latitude=mission.position.lat.decimal_degree,
                                longitude=mission.position.lon.decimal_degree,
                                elevation=mission.elevation,
                                profile=profile)

        for waypoint in profileinstance.waypoints:
            sequence = sequences_db_instances.get(waypoint.sequence)
            WaypointModel.create(name=waypoint.name,
                                 latitude=waypoint.position.lat.decimal_degree,
                                 longitude=waypoint.position.lon.decimal_degree,
                                 elevation=waypoint.elevation,
                                 profile=profile,
                                 sequence=sequence)

        for instance in delete_list:
            instance.delete_instance()

    @staticmethod
    def delete_profile(profilename):
        profile = ProfileModel.get(name=profilename)
        for mission in profile.missions:
            mission.delete_instance()

        for waypoint in profile.waypoints:
            waypoint.delete_instance()

        profile.delete_instance()

    @staticmethod
    def get_profile_names():
        return [profile.name for profile in ProfileModel.select()]

    @staticmethod
    def close():
        db.close()
