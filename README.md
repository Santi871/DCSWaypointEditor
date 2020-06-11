# DCS Waypoint Editor

Simple configurable script to input preplanned missions and waypoints coordinates into DCS aircraft. 

Currently supported aircraft:

* F/A-18C
* AV-8B
* M-2000C
* F-14A/B
* A-10C


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

1. Make sure your F10 map is in [DD MM SS.ss](https://i.imgur.com/9GIU7pJ.png) or [MGRS](https://i.imgur.com/T7lBvlx.png) coordinate format.
 You may cycle coordinate formats with `LAlt+Y`.

2. Click `Capture from DCS F10 map`

3. In the DCS F10 map, hover your mouse over your desired position

5. Press the key you bound to F10 map capture during first time setup (default is `LCtrl+T`). The results will be indicated
in the capture status textbox.

6. (Optional) Assign a name to the waypoint.

7. Click `Add` to add the waypoint to the list of active waypoints

#### F10 map quick capture

Quick capture works in a similar way to regular coordinates capturing, except it will automatically add a waypoint
at the desired position every time the F10 map capture keybind is pressed.  This can be toggled on/off with a
hotkey (default is `LCtrl+LShift+T`).

#### Preset coordinates

You may select a position from a list of preset coordinates. Coordinates for all Caucasus and PG airfields and BlueFlag
FARPS are included.

#### Hornet JDAM preplanned missions

Hornet JDAM preplanned missions work in a similar way to waypoints, however, you **must** select the correct station
for the mission to be assigned using the station selector.

#### Entering a list of waypoints into your aircraft

An optional hotkey can be assigned to enter coordinates into the aircraft.  This is done during initial setup
of the application.

##### F/A-18C

1. Make sure the main HSI page is on the AMPCD (bottom screen) if you are entering waypoints.
 
2. If you are entering JDAM preplanned missions, make sure the JDAM preplanned missions page is on the left DDI

![pages](https://i.imgur.com/Nxr9qKX.png)

3. With a list of active waypoints and/or JDAM preplanned missions, click `Enter into aircraft`

4. Tab back into DCS and let it enter everything

##### AV-8B

1. Make sure the main EHSD page is on the left AMPCD (left screen).

2. With a list of active waypoints, click `Enter into aircraft`

3. Tab back into DCS and let it enter everything

##### M-2000C

1. With a list of active waypoints, click `Enter into aircraft`

2. Tab back into DCS and let it enter everything

#### Profile saving

You may save your current list of waypoints as a profile and then load it later. Clicking `save` with a profile active
will overwrite it with the current list.

#### Export to file

If you wish to share your current profile, click `Export to file` and give it a descriptive name.

#### Import from file

Profiles may be imported from a file that was previously exported.

#### Creating your own preset locations

You may add more preset locations by adding more JSON formatted files in the data folder,
following the format in `pg.json` and `cauc.json`.

#### Exporting to encoded string

Support for exporting current profile to an encoded string has been implemented to allow for quick sharing
of waypoint and mission data to other people.  Once you have created a mission, click the `Encode to String`
button.  This will copy an encoded string to your clipboard to share with other users.

#### Importing from encoded string

Once another user has sent their encoded string to yourself, just copy the string to your clipboard (default `LCtrl+C`)
and press the `Decode from String` button in the application.  If successful, their mission data should be imported into
a new profile and a pop-up should appear letting you know import was successful.

## Known issues

* Attempting to enter sequence #2 or #3 without sequence #1 will not work.

## Donate

If you'd like to support my work, it is very much appreciated!

[![paypal](https://www.paypalobjects.com/en_US/i/btn/btn_donate_LG.gif)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=U6ZGEE7PF6KAG&source=url)

## About DCS-BIOS
DCS-BIOS is redistributed under GPLv3 license.

DCS-BIOS: https://github.com/DCSFlightpanels/dcs-bios

## Other credits

[PyMGRS](https://github.com/aydink/pymgrs) by aydink
