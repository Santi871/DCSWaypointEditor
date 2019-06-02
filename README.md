# Hornet Waypoint Editor

Simple configurable script to input preplanned missions and waypoints coordinates into DCS aircraft. 

Currently, only the DCS F/A-18C is supported, but other aircraft support is planned.


## Installation

1. Download and install [Google Tesseract](https://github.com/UB-Mannheim/tesseract/wiki)
2. Unzip the contents of the DCS-Waypoint-Editor ZIP to a folder
3. Run `dcs_wp_editor.exe` and perform the first time setup.

## Usage

Waypoints and JDAM preplanned missions can be added by either manually entering a set of coordinates or capturing them
from the DCS F10 map via optical text recognition. 

#### Manual coordinates entry

1. Choose a waypoint type (WP = regular waypoint, MSN = JDAM preplanned mission)

2. Enter the latitude and longitude. Decimal seconds are supported.

3. Enter the elevation in feet (optional for regular waypoints, mandatory for JDAM preplanned missions)

5. (Optional) Choose a sequence to assign the waypoint to.

6. (Optional) Assign a name to the waypoint.

7. Click `Add` to add the waypoint to the list of active waypoints

#### F10 map captured coordinates entry

1. Make sure your F10 map is in DD MM SS.ss coordinate format. You may cycle coordinate formats with `LAlt+Y`.

2. Click `Capture from DCS F10 map`

3. In the DCS F10 map, hover your mouse over your desired position

5. Press the key you bound to F10 map capture during first time setup (default is `LCtrl+T`). The results will be indicated
in the capture status textbox.

6. (Optional) Assign a name to the waypoint.

7. Click `Add` to add the waypoint to the list of active waypoints

#### F10 map quick capture

 Quick capture works in a similar way to regular coordinates capturing, except it will automatically add a waypoint
at the desired position every time the F10 map capture keybind is pressed.

#### Preset coordinates

You may select a position from a list of preset coordinates. Coordinates for all Caucasus and PG airfields and BlueFlag
FARPS are included.

#### Entering a list of waypoints into your aircraft

Currently, this feature is only supported in the F/A-18C Hornet.

1. Make sure the main HSI page is on the AMPCD (bottom screen) if you are entering waypoints.
 
2. If you are entering JDAM preplanned missions, make sure the main JDAM page is on the left DDI (the page immediately 
after selecting a JDAM from the stores page).

3. With a list of active waypoints and/or JDAM preplanned missions, click `Enter into aircraft`

4. Tab back into DCS and let it enter everything

#### Profile saving

You may save your current list of waypoints as a profile and then load it later. Clicking `save` with a profile active
will overwrite it with the current list.

#### Export to file

If you wish to share your current profile, click `Export to file` and give it a descriptive name.

#### Import from file

Profiles may be imported from a file that was previously exported.

## Known issues

* Attempting to enter sequence #2 or #3 without sequence #1 will not work.

## About DCS-BIOS
DCS-BIOS is redistributed under GPLv3 license.

DCS-BIOS: https://github.com/DCSFlightpanels/dcs-bios