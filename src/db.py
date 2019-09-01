from src.models import ProfileModel, WaypointModel, SequenceModel, db
from src.logger import get_logger


class DatabaseInterface:
    def __init__(self, db_name):
        self.logger = get_logger("db")
        db.init(db_name)
        db.connect()
        db.create_tables([ProfileModel, WaypointModel, SequenceModel])
        self.logger.debug("Connected to database")

    @staticmethod
    def close():
        db.close()
