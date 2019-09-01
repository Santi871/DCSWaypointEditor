from time import sleep
from src.objects import default_bases
from src.db import DatabaseInterface
from src.logger import get_logger
from src.drivers import HornetDriver, HarrierDriver, MirageDriver, TomcatDriver, DriverException, WarthogDriver


class WaypointEditor:

    def __init__(self, settings):
        self.logger = get_logger("driver")
        self.settings = settings
        self.db = DatabaseInterface(settings['PREFERENCES'].get("DB_Name", "profiles.db"))
        self.default_bases = default_bases
        self.drivers = dict(hornet=HornetDriver(self.logger, settings),
                            harrier=HarrierDriver(self.logger, settings),
                            mirage=MirageDriver(self.logger, settings),
                            tomcat=TomcatDriver(self.logger, settings),
                            warthog=WarthogDriver(self.logger, settings))
        self.driver = self.drivers["hornet"]

    def set_driver(self, driver_name):
        try:
            self.driver = self.drivers[driver_name]
        except KeyError:
            raise DriverException(f"Undefined driver: {driver_name}")

    def enter_all(self, profile):
        self.logger.info(f"Entering waypoints for aircraft: {profile.aircraft}")
        sleep(int(self.settings['PREFERENCES'].get('Grace_Period', 5)))
        self.driver.enter_all(profile)

    def stop(self):
        self.db.close()
        if self.driver is not None:
            self.driver.stop()
