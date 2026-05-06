"""
operator_launch.py
==================
Launch one or more operator profiles.

Single operator
---------------
ros2 launch robotic_arm_controls operator_launch.py profiles:=sameed

Multiple operators (active + standby)
--------------------------------------
ros2 launch robotic_arm_controls operator_launch.py profiles:=sameed,alice

Per profile this starts:
  - One joy_node per controller slot (controller_1, controller_2)
  - One arm_controller_node

arm_controller_node lives under a namespace matching the profile id:
  /sameed/arm_controller_node

joy_nodes are NOT namespaced — they use unique node names instead:
  joy_sameed_controller_1
  joy_sameed_controller_2

Device resolution priority (handled in _joy_node / DeviceSpec.resolve_dev_path):
  1. dev_path  — by-id filename, stable across reboots, preferred
  2. device_id — integer jsN index, fragile, avoid unless necessary
  3. glob      — auto-detected from devices.yaml dev_paths patterns

VirtualBox note:
  joy_node 3.3.0 ignores the dev= string parameter; device_id (integer) is
  used instead, resolved from the by-id joystick symlink at launch time.
  VirtualBox USB passthrough serialises device opens, so joy_nodes are
  chained via OnProcessStart + TimerAction rather than launched in parallel.
  This staggering is not needed on real hardware.
"""

import os

import yaml
import launch_ros.actions
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction, TimerAction, RegisterEventHandler
from launch.event_handlers import OnProcessStart
from launch.substitutions import LaunchConfiguration

PKG = "robotic_arm_controls"

# Seconds to wait after a joy_node process starts before launching the next.
# Needed under VirtualBox to avoid USB passthrough serialisation deadlock.
# Set to 0.0 on real hardware.
JOY_NODE_START_DELAY = 3.0


def _cfg(relative: str) -> str:
    return os.path.join(get_package_share_directory(PKG), "config", relative)


def _joy_node(
    slot: dict,
    topic: str,
    node_name: str,
) -> launch_ros.actions.Node:
    """
    Launch a joy_node for one controller slot.

    Device is located by priority:
      1. dev_path  — by-id filename from operator YAML.
                     Resolved to a device_id integer at launch time because
                     joy_node 3.3.0 ignores the dev= string parameter.
                     The -event-joystick suffix is swapped for -joystick to
                     reach the jsN symlink that joy_node actually scans.
      2. device_id — integer jsN index from operator YAML (fragile,
                     enumeration-order dependent, avoid if dev_path works).
      3. neither   — joy_node opens /dev/input/js0 by default.

    No namespace is set so that the /joy remapping works as a simple
    absolute-topic override without namespace interference.
    """
    dev_path  = slot.get("dev_path")
    device_id = slot.get("device_id")

    if dev_path is not None:
        full_path = f"/dev/input/by-id/{dev_path}"
        if not os.path.exists(full_path):
            raise FileNotFoundError(
                f"[{node_name}] dev_path not found: {full_path}\n"
                f"  Available by-id entries:\n"
                + "\n".join(f"    {e}" for e in sorted(os.listdir("/dev/input/by-id")))
            )

        # joy_node 3.3.0 scans /dev/input/js* not event*, so resolve the
        # -joystick symlink and extract the jsN integer.
        js_path = dev_path.replace("-event-joystick", "-joystick")
        js_full = f"/dev/input/by-id/{js_path}"
        if not os.path.exists(js_full):
            raise FileNotFoundError(
                f"[{node_name}] Cannot resolve js device for {dev_path}\n"
                f"  Expected: {js_full}"
            )

        real    = os.path.realpath(js_full)   # e.g. /dev/input/js2
        js_num  = int(real.replace("/dev/input/js", ""))
        print(f"DEBUG: {node_name} using device_id={js_num} (resolved from {js_full} -> {real})")
        params = [{"device_id": js_num, "autorepeat_rate": 20.0}]

    elif device_id is not None:
        params = [{"device_id": int(device_id), "autorepeat_rate": 20.0}]

    else:
        params = [{"autorepeat_rate": 20.0}]

    return launch_ros.actions.Node(
        package="joy",
        executable="joy_node",
        name=node_name,
        parameters=params,
        remappings=[("/joy", topic)],
        output="screen",
    )


def _launch_setup(context, *args, **kwargs):
    profiles_str = LaunchConfiguration("profiles").perform(context)
    profile_ids  = [p.strip() for p in profiles_str.split(",") if p.strip()]

    actions: list = []
    seen_topics: set[str] = set()

    for profile_id in profile_ids:
        profile_yaml = _cfg(f"operators/{profile_id}.yaml")
        if not os.path.exists(profile_yaml):
            raise FileNotFoundError(f"Operator profile not found: {profile_yaml}")

        print(f"DEBUG: Loading profile from {profile_yaml}")

        with open(profile_yaml) as f:
            raw = yaml.safe_load(f)

        ros_params = (
            raw.get("arm_controller_node")
            or raw.get("/**")
            or {}
        ).get("ros__parameters", {})

        # arm_controller_node — namespaced per profile
        actions.append(launch_ros.actions.Node(
            package=PKG,
            executable="arm_controller_node",
            name="arm_controller_node",
            namespace=profile_id,
            parameters=[ros_params],
            output="screen",
            emulate_tty=True,
        ))

        # joy_nodes — no namespace, unique name per profile+slot.
        # Collected first, then chained via OnProcessStart so that each node
        # starts only after the previous one has spawned (VirtualBox workaround).
        joy_nodes: list = []

        for ctrl_key in ("controller_1", "controller_2"):
            topic     = ros_params.get(f"{ctrl_key}.topic")
            dev_path  = ros_params.get(f"{ctrl_key}.dev_path")
            device_id = ros_params.get(f"{ctrl_key}.device_id")

            if topic is None:
                continue
            if topic in seen_topics:
                continue
            seen_topics.add(topic)

            print(
                f"DEBUG: {profile_id}/{ctrl_key} "
                f"topic={topic}  "
                f"dev_path={dev_path}  "
                f"device_id={device_id}"
            )

            slot = {"dev_path": dev_path, "device_id": device_id}
            joy_nodes.append(_joy_node(
                slot,
                topic,
                node_name=f"joy_{profile_id}_{ctrl_key}",
            ))

        # Launch first joy_node immediately; chain each subsequent one to
        # start JOY_NODE_START_DELAY seconds after the previous one spawns.
        if joy_nodes:
            actions.append(joy_nodes[0])
            for i in range(1, len(joy_nodes)):
                actions.append(RegisterEventHandler(
                    OnProcessStart(
                        target_action=joy_nodes[i - 1],
                        on_start=[TimerAction(
                            period=JOY_NODE_START_DELAY,
                            actions=[joy_nodes[i]],
                        )],
                    )
                ))

    return actions


def generate_launch_description() -> LaunchDescription:
    return LaunchDescription([
        DeclareLaunchArgument(
            "profiles",
            default_value="sameed",
            description=(
                "Comma-separated operator profile names. "
                "Each must have a matching file in config/operators/. "
                "Example: profiles:=sameed,alice"
            ),
        ),
        OpaqueFunction(function=_launch_setup),
    ])