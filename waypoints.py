from objects import Wp, MSN
from LatLon23 import LatLon, Latitude, Longitude

active_wps = (

    Wp("Qeshm"),


)

active_msns = (
    MSN("40RBQ8359136367", 75),

    MSN(LatLon(Latitude(degree=55, minute=23, second=33.25), Longitude(degree=55, minute=23, second=33.25)), 75)
)


keybinds = {
    "ufc_0": "shift+0",
    "ufc_1": "shift+1",
    "ufc_2": "shift+2",
    "ufc_3": "shift+3",
    "ufc_4": "shift+4",
    "ufc_5": "shift+5",
    "ufc_6": "shift+6",
    "ufc_7": "shift+7",
    "ufc_8": "shift+8",
    "ufc_9": "shift+9",
    "ufc_enter": "ctrl+8",
    "ufc_pos": "ctrl+7",
    "ufc_hgt": "ctrl+6",
    "ufc_clr": "ctrl+5",
    "hsi_data": "ctrl+d",
    "hsi_ufc": "ctrl+0",
    "hsi_arrowup": "ctrl+9",
    "hsi_aawp": "ctrl+4",
    "lddi_pb4": "alt+9",
    "lddi_pb6": "alt+1",
    "lddi_pb7": "alt+2",
    "lddi_pb8": "alt+3",
    "lddi_pb9": "alt+4",
    "lddi_pb10": "alt+5",
    "lddi_pb11": "alt+6",
    "lddi_pb14": "alt+7",
    "lddi_pb19": "alt+8",
    "ufc_pb4": "ctrl+1",
}
