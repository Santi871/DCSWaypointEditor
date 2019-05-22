import PySimpleGUI as PyGUI


def get_gui(active_wps, active_msns):
    actives_list = [f"WP{i + 1}" for i in range(len(active_wps))]
    actives_list += [f"MSN{i + 1}" for i in range(len(active_msns))]

    framecoordslayout = [
        [PyGUI.Text("Degrees")],
        [PyGUI.InputText(size=(40, 1))],
        [PyGUI.Text("Minutes")],
        [PyGUI.InputText(size=(40, 1))],
        [PyGUI.Text("Seconds")],
        [PyGUI.InputText(size=(40, 1), pad=(5, (3, 10)))],
    ]

    frameelevationlayout = [
        [PyGUI.Text("Feet")],
        [PyGUI.InputText(size=(40, 1))],
        [PyGUI.Text("Meters")],
        [PyGUI.InputText(size=(40, 1), pad=(5, (3, 10)))],
    ]

    framedatalayoutcol1 = [
        [PyGUI.Text("Nr")],
        [PyGUI.InputText(size=(40, 1), pad=(5, (3, 10)))],
    ]

    framedatalayoutcol2 = [
        [PyGUI.Text("Name")],
        [PyGUI.InputText(size=(40, 1), pad=(5, (3, 10)))],
    ]

    framelongitude = PyGUI.Frame("Longitude", framecoordslayout)
    framelatitude = PyGUI.Frame("Latitude", framecoordslayout)
    frameelevation = PyGUI.Frame("Elevation", frameelevationlayout)
    framedata = PyGUI.Frame("Data", [[PyGUI.Column(framedatalayoutcol1), PyGUI.Column(framedatalayoutcol2)]],
                            pad=((20, 5), 3))

    col0 = [
        [PyGUI.Listbox(values=actives_list, size=(30, 24), enable_events=True)],
        [PyGUI.Button("Add waypoint", size=(26, 1))],
        [PyGUI.Button("Add mission", size=(26, 1))],
        [PyGUI.Button("Save profile", size=(12, 1)), PyGUI.Button("Load profile", size=(12, 1))],
        [PyGUI.Button("Export to file", size=(12, 1)), PyGUI.Button("Import from file", size=(12, 1))],
    ]

    col1 = [
        [framelatitude],
        [frameelevation]
    ]

    col2 = [
        [framelongitude]
    ]

    colmain1 = [
        [framedata],
        [PyGUI.Column(col1), PyGUI.Column(col2)],
    ]

    layout = [
        [PyGUI.Column(col0), PyGUI.Column(colmain1)],
    ]

    return PyGUI.Window('Hornet Waypoint Editor', layout)


def run_gui(window):
    while True:
        event, values = window.Read()
        print(str(event))
        print(str(values))

        if event is None or event == 'Exit':
            break
    exit(0)
