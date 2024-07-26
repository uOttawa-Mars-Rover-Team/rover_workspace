import argparse
import json
import os
import re
import subprocess
from typing import Any

import urwid


class CameraControlApp:

    ON_LABEL = "ON"
    OFF_LABEL = "OFF"
    button_options = [OFF_LABEL, ON_LABEL]

    def __init__(self, title: str, cameras: dict[str, str]):
        self.title = title
        # Ensure camera names match regex to allow for namespaces to be created based
        # on each camera's name
        regex = r"^[a-zA-Z0-9_]+$"
        assert all(
            [re.search(regex, name) is not None for name in cameras]
        ), f"Each camera name must match the regex: {regex}"
        self.cameras = cameras
        # Keep track of launched processes
        self.camera_handles = {name: None for name in self.cameras}
        # Keep a history of events and commands if necessary for debugging
        self.event_history = []
        self.command_history = []

    def run(self):
        """
        Start the loop to run the app.
        """
        menu = self.menu()
        overlay = urwid.Overlay(
            menu,
            urwid.SolidFill("\N{MEDIUM SHADE}"),
            align=urwid.CENTER,
            width=(urwid.RELATIVE, 60),
            valign=urwid.MIDDLE,
            height=(urwid.RELATIVE, 60),
            min_width=60,
            min_height=9,
        )
        urwid.MainLoop(
            overlay,
            palette=[("reversed", "standout", "")],
            unhandled_input=self.handle_input,
        ).run()

    def menu(self) -> urwid.Padding:
        """
        Generates a urwid-compatible menu for the app.
        """
        body = [urwid.Divider(), urwid.Text(self.title), urwid.Divider()]

        pile_cells = []

        for camera_name in self.cameras:
            cells = [urwid.Text(camera_name)]
            radio_button_group = []
            # Use a radio button with an option to turn on or off a given camera
            cells += [
                urwid.RadioButton(
                    radio_button_group,
                    option,
                    on_state_change=self.handle_change,
                    user_data=(camera_name),
                )
                for option in self.button_options
            ]
            # Layout the camera's name and the radio buttons with GridFlow
            pile_cells.append(
                urwid.GridFlow(
                    cells,
                    cell_width=10,
                    h_sep=4,
                    v_sep=1,
                    align="left",
                )
            )
            # Add a divider for spacing
            pile_cells.append(urwid.Divider())

        body.append(
            urwid.Padding(
                urwid.Pile(pile_cells),
                left=3,
                right=3,
            ),
        )

        listbox = urwid.ListBox(urwid.SimpleListWalker(body))
        return urwid.Padding(listbox, left=2, right=2)

    def handle_change(
        self, radio_button: urwid.RadioButton, new_state: bool, user_data: Any
    ) -> None:
        """
        Handle change of a camera's RadioButton selection.
        """
        # The user data should only contain the camera name
        camera_name = user_data
        # Only keep track of whether the "ON" button is selected or deselected
        if radio_button.label == "ON":
            self.set_camera_state(camera_name, new_state)
            self.event_history.append((radio_button, new_state, camera_name))

    def set_camera_state(self, camera_name: str, state: bool) -> None:
        """
        Turn a specified camera on or off.
        """
        params_file_path = self.cameras[camera_name]
        # Turn the camera on
        if state:
            # Launch the given camera using a unique namespace, passing in the
            # relevant params file
            cmd = f"ros2 run usb_cam usb_cam_node_exe --ros-args --remap __ns:=/usb_cam_{camera_name} --params-file {params_file_path}"
            process = subprocess.Popen(
                cmd.split(), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            self.camera_handles[camera_name] = process
            self.command_history.append(cmd)
        # Turn the camera off
        else:
            # Kill the process started earlier
            process = self.camera_handles[camera_name]
            process.kill()
            self.camera_handles[camera_name] = None
            # Kill any child processes using pkill and a string filter to
            # search for running processes with
            cmd = f'pkill -f "__ns:=/usb_cam_{camera_name} --params-file {params_file_path}"'
            subprocess.run(
                cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            self.command_history.append(cmd)

    def handle_input(self, key: str) -> None:
        if key in ("q", "Q"):
            for camera, val in self.camera_handles.items():
                if val is not None:
                    self.set_camera_state(camera, False)
            raise urwid.ExitMainLoop()


def main():
    parser = argparse.ArgumentParser(
        description="Launch and shutdown ROS publishers for cameras."
    )
    parser.add_argument(
        "config_path",
        metavar="config_path",
        type=str,
        nargs=1,
        help="The path to the JSON config file being used.",
    )
    args = parser.parse_args()

    with open(args.config_path[0]) as f:
        config = json.load(f)

    title = config["title"]
    cameras = config["cameras"]
    # Replace non-full paths to camera YAML configs with full paths
    for camera_name, config_path in cameras.items():
        if os.sep not in config_path:
            cameras[camera_name] = os.path.join(
                os.path.dirname(os.path.abspath(args.config_path[0])), config_path
            )

    app = CameraControlApp(title, cameras)
    app.run()


if __name__ == "__main__":
    main()
