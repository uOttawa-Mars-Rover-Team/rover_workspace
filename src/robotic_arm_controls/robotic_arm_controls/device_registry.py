"""
device_registry.py
==================
Loads devices.yaml and resolves logical axis/button names to raw Joy indices.
Used by arm_controller.py when operator configs use logical names.
Falls back gracefully if devices.yaml is not found.
"""
from __future__ import annotations

import glob
import os
from pathlib import Path
from typing import Optional

import yaml


class DeviceSpec:
    def __init__(self, category: str, device_id: str, data: dict):
        self.category         = category
        self.device_id        = device_id
        self.name: str        = data.get("name", device_id)
        self.dev_paths: list[str] = data.get("dev_paths", [])
        self.expected_buttons: int = data.get("buttons", -1)
        self.expected_axes:    int = data.get("axes",    -1)
        self.axis_map:   dict[str, int] = data.get("axis_map",   {})
        self.button_map: dict[str, int] = data.get("button_map", {})

    def raw_axis(self, logical: str) -> int:
        """Return raw Joy axis index for a logical name, -1 if not found."""
        return self.axis_map.get(logical, -1)

    def raw_button(self, logical: str) -> int:
        """Return raw Joy button index for a logical name, -1 if not found."""
        return self.button_map.get(logical, -1)

    def matches_joy_msg(self, num_buttons: int, num_axes: int) -> bool:
        btn_ok = self.expected_buttons == -1 or num_buttons == self.expected_buttons
        ax_ok  = self.expected_axes    == -1 or num_axes    == self.expected_axes
        return btn_ok and ax_ok

    def resolve_dev_path(
        self,
        override_dev_path: Optional[str] = None,
        override_device_id: Optional[int] = None,
    ) -> Optional[str]:
        """
        Resolve to a concrete /dev/input path. Priority:

          1. override_dev_path  — exact by-id filename from operator YAML.
             Tried directly under /dev/input/by-id/. This is the most
             reliable method: stable across reboots, immune to enumeration
             order, and unique even when multiple units of the same model
             are connected (serial numbers disambiguate).

          2. override_device_id — integer jsN index from operator YAML.
             Only used when no dev_path is given. Fragile: the mapping from
             integer to physical device depends on plug-in order and can
             shift between boots or when other USB devices are added.

          3. dev_paths glob     — patterns from devices.yaml, matched under
             /dev/input/by-id/. Used when the operator YAML provides neither
             dev_path nor device_id. Patterns must include a trailing * to
             absorb serial-number suffixes that manufacturers embed in the
             by-id name (e.g. Logitech_Gamepad_F310_FA73A900). Without the
             wildcard the glob produces no matches and this method silently
             falls through to None.
        """
        base = "/dev/input/by-id"

        # --- Priority 1: exact by-id filename from operator YAML -------------
        if override_dev_path:
            full = os.path.join(base, override_dev_path)
            if os.path.exists(full):
                return full
            # Warn-worthy: operator explicitly named a path that doesn't exist
            # (caller should log this; we just return None to surface the miss)
            return None

        # --- Priority 2: integer device_id from operator YAML ----------------
        if override_device_id is not None:
            # Return as string; joy_node accepts "device_id" integer param
            return str(override_device_id)

        # --- Priority 3: glob patterns from devices.yaml ---------------------
        if os.path.isdir(base):
            for pattern in self.dev_paths:
                matches = glob.glob(os.path.join(base, pattern))
                if matches:
                    # Prefer event-joystick over plain joystick symlink:
                    # event-joystick gives raw evdev input (more axes/buttons),
                    # joystick gives the legacy joydev interface (fewer axes).
                    event_matches = [m for m in matches if "event" in m]
                    return event_matches[0] if event_matches else matches[0]

        return None


class DeviceRegistry:
    def __init__(self, categories: dict[str, dict[str, DeviceSpec]]):
        self._categories = categories

    @classmethod
    def from_yaml(cls, path: str | Path) -> "DeviceRegistry":
        with open(path) as f:
            data = yaml.safe_load(f)

        categories: dict[str, dict[str, DeviceSpec]] = {}
        for cat_name, cat_data in data.get("categories", {}).items():
            devices: dict[str, DeviceSpec] = {}
            for dev_id, dev_data in cat_data.get("devices", {}).items():
                devices[dev_id] = DeviceSpec(cat_name, dev_id, dev_data)
            categories[cat_name] = devices

        return cls(categories)

    def get_device(self, category: str, device_id: str) -> Optional[DeviceSpec]:
        return self._categories.get(category, {}).get(device_id)

    def detect_device(
        self, category: str, num_buttons: int, num_axes: int
    ) -> Optional[DeviceSpec]:
        """Return first device in category matching button/axis counts."""
        for spec in self._categories.get(category, {}).values():
            if spec.matches_joy_msg(num_buttons, num_axes):
                return spec
        return None