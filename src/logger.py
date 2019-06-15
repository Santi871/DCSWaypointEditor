import logging
from sys import stdout


def log_settings():
    with open("log.txt", "w+") as f:
        f.write("----settings.ini----\n\n")
        with open("settings.ini", "r") as f2:
            f.writelines(f2.readlines())

        f.write("\n\n--------------------\n\n")


def get_logger(name):
    logger = logging.getLogger(name)
    formatter = logging.Formatter('%(asctime)s:%(name)s: %(levelname)s - %(message)s')
    s_handler = logging.StreamHandler(stdout)
    s_handler.setFormatter(formatter)
    f_handler = logging.FileHandler('log.txt', encoding="utf-8")
    f_handler.setFormatter(formatter)
    logger.addHandler(f_handler)
    logger.addHandler(s_handler)
    logger.setLevel(logging.DEBUG)

    return logger
