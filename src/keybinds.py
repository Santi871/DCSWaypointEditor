from pathlib import Path
from slpp import slpp as lua


reformers = {
    'lctrl': "left ctrl",
    'lalt': "left alt",
    'lshift': "left shift",
    'rctrl': "right ctrl",
    'ralt': "right alt",
    'rshift': "right shift",
}


def parse_reformers(bind):
    bindstr = ""

    if bind.get('reformers') is not None:
        for _, reformer in bind.get('reformers').items():
            bindstr += (reformers[reformer.lower()] + "+")

    return bindstr


def parse_dcs_binds(using_openbeta):
    parsed_binds = dict()

    if using_openbeta:
        dcs_path = f"{str(Path.home())}\\Saved Games\\DCS.openbeta\\Config\\Input\\FA-18C_hornet\\keyboard"
    else:
        dcs_path = f"{str(Path.home())}\\Saved Games\\DCS\\Config\\Input\\FA-18C_hornet\\keyboard"

    with open(dcs_path + "\\Keyboard.diff.lua", mode="r") as f:
        c = f.read()

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
            parsed_binds[f'LMDI_PB{name[-1:]}'] = bindstr
        elif "AMPCD PB" in name:
            parsed_binds[f'AMPCD_PB{name[-1:]}'] = bindstr

    return parsed_binds


class BindError(Exception):
    pass


class BindsManager:
    def __init__(self, logger, settings):
        self.settings = settings
        self.preferences = self.settings['PREFERENCES']
        self.logger = logger

        self.binds_dict = parse_dcs_binds(self.preferences.getboolean('Using_OpenBeta'))

    def get_bind(self, bindname):
        bind = self.binds_dict.get(bindname)

        if bind is None:
            raise BindError(f"Bind {bindname} is undefined")
        return bind

    def ufc(self, num):
        return self.get_bind(f"UFC_{num}")

    def lmdi(self, pb):
        return self.get_bind(f"LMDI_PB{pb}")

    def ampcd(self, pb):
        return self.get_bind(f"AMPCD_PB{pb}")
