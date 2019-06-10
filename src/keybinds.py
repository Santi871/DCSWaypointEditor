from pathlib import Path
from slpp import slpp as lua
import keyboard
from time import sleep
import socket


reformers = {
    'lctrl': "left ctrl",
    'lalt': "left alt",
    'lshift': "left shift",
    'lwin': "left windows",
    'rctrl': "right ctrl",
    'ralt': "right alt",
    'rshift': "right shift",
    'rwin': "right windows",
}


def parse_reformers(bind):
    bindstr = ""

    if bind.get('reformers') is not None:
        for _, reformer in bind.get('reformers').items():
            bindstr += (reformers[reformer.lower()] + "+")

    return bindstr


def parse_dcs_binds(dcs_path):
    parsed_binds = dict()

    dcs_path = f"{dcs_path}\\Config\\Input\\FA-18C_hornet\\keyboard"

    try:
        with open(dcs_path + "\\Keyboard.diff.lua", mode="r") as f:
            c = f.read()
    except FileNotFoundError:
        return None

    i = c.find("{")
    e = c.find("return")
    d = lua.decode(c[i:e])

    for _, bind in d.get('keyDiffs').items():
        name = bind.get('name')

        try:
            bind = bind.get('added').get(1)
        except AttributeError:
            continue

        bindstr = parse_reformers(bind)
        bindstr += bind.get('key')

        if "UFC Option Select Pushbutton" in name:
            parsed_binds[f'UFC_OSB{name[-1:]}'] = bindstr
        elif "UFC Keyboard Pushbutton" in name and "CLR" not in name and "ENT" not in name:
            parsed_binds[f'UFC_{name[-1:]}'] = bindstr
        elif "UFC Keyboard Pushbutton" in name and ("CLR" in name or "ENT" in name):
            parsed_binds[f'UFC_{name[-3:]}'] = bindstr
        elif "Left MDI PB" in name:
            parsed_binds[f'LMDI_PB{name[-2:]}'.replace(' ', '')] = bindstr
        elif "AMPCD PB" in name:
            parsed_binds[f'AMPCD_PB{name[-2:]}'.replace(' ', '')] = bindstr

    return parsed_binds


class BindError(Exception):
    pass


class BindsPresser:
    def __init__(self):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.host, self.port = '127.0.0.1', 7778

    def press_with_delay(self, key, delay_after=0.2, delay_release=0.2, use_socket=False):
        if not key:
            return

        if not use_socket:
            keyboard.press(key)
        else:
            self.s.sendto(f"{key} 1\n".replace("OSB", "OS").encode("utf-8"), (self.host, self.port))

        sleep(delay_release)
        if not use_socket:
            keyboard.release(key)
        else:
            self.s.sendto(f"{key} 0\n".replace("OSB", "OS").encode("utf-8"), (self.host, self.port))

        sleep(delay_after)


class BindsManager:
    def __init__(self, mode, logger, preferences):
        self.mode = mode
        self.logger = logger
        # self.binds_dict = parse_dcs_binds(preferences.get("dcs_path"))
        self.binds_dict = dict()
        self.p = BindsPresser()

    def get_bind(self, bindname):
        bind = self.binds_dict.get(bindname)

        if bind is None:
            raise BindError(f"Bind {bindname} is undefined")
        return bind

    def ufc(self, num, delay_after=0.2, delay_release=0.2):
        key = str()
        use_socket = False

        if self.mode == "keyboard":
            key = self.get_bind(f"UFC_{num}")
        elif self.mode == "dcs-bios":
            key = f"UFC_{num}"
            use_socket = True

        self.p.press_with_delay(key, delay_after=delay_after, delay_release=delay_release, use_socket=use_socket)

    def lmdi(self, pb, delay_after=0.2, delay_release=0.2):
        key = str()
        use_socket = False

        if self.mode == "keyboard":
            key = self.get_bind(f"LMDI_PB{pb}")
        elif self.mode == "dcs-bios":
            key = f"LEFT_DDI_PB_{pb.zfill(2)}"
            use_socket = True

        self.p.press_with_delay(key, delay_after=delay_after, delay_release=delay_release, use_socket=use_socket)

    def ampcd(self, pb, delay_after=0.2, delay_release=0.2):
        key = str()
        use_socket = False

        if self.mode == "keyboard":
            key = self.get_bind(f"AMPCD_PB{pb}")

        elif self.mode == "dcs-bios":
            key = f"AMPCD_PB_{pb.zfill(2)}"
            use_socket = True

        self.p.press_with_delay(key, delay_after=delay_after, delay_release=delay_release, use_socket=use_socket)
