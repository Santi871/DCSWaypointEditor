import unittest
import logging
import configparser
import src.drivers as drivers

logger = logging.getLogger()
config = configparser.ConfigParser()
config.read("../fixtures/settings.ini")


class TestBaseDriver(unittest.TestCase):
    def setUp(self) -> None:
        self.driver = drivers.BaseDriver(logger, config)

    def test_send(self):
        self.assertTrue(self.driver.press_with_delay("UFC_1"))

    def test_send_raw(self):
        self.assertTrue(self.driver.press_with_delay("RIO_CAP_CATRGORY 3"))
