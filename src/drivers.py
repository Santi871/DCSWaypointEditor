import socket
from time import sleep


class Driver:
    def __init__(self, host="127.0.0.1", port=7778):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.host, self.port = host, port

    def press_with_delay(self, key, delay_after=0.2, delay_release=0.2):
        if not key:
            return

        # TODO get rid of the OSB -> OS replacement
        self.s.sendto(f"{key} 1\n".replace("OSB", "OS").encode("utf-8"), (self.host, self.port))
        sleep(delay_release)

        self.s.sendto(f"{key} 0\n".replace("OSB", "OS").encode("utf-8"), (self.host, self.port))
        sleep(delay_after)

    def stop(self):
        self.s.close()


class HornetDriver(Driver):
    def ufc(self, num, delay_after=0.2, delay_release=0.2):
        key = f"UFC_{num}"
        self.press_with_delay(key, delay_after=delay_after, delay_release=delay_release)

    def lmdi(self, pb, delay_after=0.2, delay_release=0.2):
        key = f"LEFT_DDI_PB_{pb.zfill(2)}"
        self.press_with_delay(key, delay_after=delay_after, delay_release=delay_release)

    def ampcd(self, pb, delay_after=0.2, delay_release=0.2):
        key = f"AMPCD_PB_{pb.zfill(2)}"
        self.press_with_delay(key, delay_after=delay_after, delay_release=delay_release)


class HarrierDriver(Driver):
    def ufc(self, num, delay_after=0.2, delay_release=0.2):
        if num not in ("ENT", "CLR"):
            key = f"UFC_B{num}"
        elif num == "ENT":
            key = "UFC_ENTER"
        elif num == "CLR":
            key = "UFC_CLEAR"
        else:
            key = f"UFC_{num}"
        self.press_with_delay(key, delay_after=delay_after, delay_release=delay_release)

    def odu(self, num, delay_after=0.2, delay_release=0.2):
        key = f"ODU_OPT{num}"
        self.press_with_delay(key, delay_after=delay_after, delay_release=delay_release)

    def lmpcd(self, pb, delay_after=0.2, delay_release=0.2):
        key = f"MPCD_L_{pb}"
        self.press_with_delay(key, delay_after=delay_after, delay_release=delay_release)
