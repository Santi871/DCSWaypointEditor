import logging
from sys import stdout


with open("log.txt", "w+") as f:
    f.write("\n\n----settings.ini----\n\n")
    with open("settings.ini", "r") as f2:
        f.writelines(f2.readlines())

    f.write("\n\n--------------------\n\n")


logger = logging.getLogger('root')
formatter = logging.Formatter('%(levelname)s - %(message)s')
s_handler = logging.StreamHandler(stdout)
s_handler.setFormatter(formatter)
f_handler = logging.FileHandler('log.txt')
f_handler.setFormatter(formatter)
logger.addHandler(f_handler)
logger.addHandler(s_handler)
logger.setLevel(logging.INFO)
