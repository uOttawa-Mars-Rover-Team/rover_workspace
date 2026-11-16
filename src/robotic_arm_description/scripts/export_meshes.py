import json
import struct
import zipfile
from pathlib import Path

import numpy as np
from scipy.spatial import ConvexHull

workspace = Path.cwd()
package = workspace / "src/robotic_arm_description"
report = workspace / "arm_cad_report_20261108_161022.txt"
archive = workspace / "Mersh.zip"

components = {}
mates = {}
current = None
entity = None

for line in report.read_text().splitlines():
    fields = line.split("\t")
    key, values = fields[0], fields[1:]

    if key == "component":
        current = components.setdefault(values[0], {})
    elif key == "mate":
        current = mates.setdefault(values[0], {"entities": []})
    elif key == "entity":
        entity = {}
        current["entities"].append(entity)
    elif key in ("end_component", "end_mate"):
        current = None
        entity = None
    elif entity is not None:
        entity[key] = values
    elif current is not None:
        current[key] = values

dtype = np.dtype([
    ("normal", "<f4", 3),
    ("vertices", "<f4", (3, 3)),
    ("attribute", "<u2"),
])


def read_stl(data):
    count = struct.unpack_from("<I", data, 80)[0]
    if len(data) != 84 + 50 * count:
        raise ValueError("Expected a binary STL file")
    triangles = np.frombuffer(
        data, dtype=dtype, offset=84
    )["vertices"].astype(float)
    if not np.isfinite(triangles).all():
        raise ValueError("Invalid mesh coordinates")
    return triangles


def write_stl(path, triangles):
    output = np.zeros(len(triangles), dtype=dtype)
    normals = np.cross(
        triangles[:, 1] - triangles[:, 0],
        triangles[:, 2] - triangles[:, 0],
    )
    lengths = np.linalg.norm(normals, axis=1)
    valid = lengths > 1e-15
    normals[valid] /= lengths[valid, None]
    output["normal"] = normals
    output["vertices"] = triangles
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(
        b"Arm mesh: metres".ljust(80, b"\0")
        + struct.pack("<I", len(output))
        + output.tobytes()
    )


# Rotate CAD Y-up coordinates into ROS Z-up coordinates.
cad_to_ros = np.array([
    [1, 0, 0],
    [0, 0, -1],
    [0, 1, 0],
])

points = {}
axes = {}

for index in range(1, 7):
    name = f"Concentric{index}"
    mate = mates[name]
    if mate["suppressed"] != ["False"]:
        raise ValueError(f"{name} is suppressed")

    first, second = [
        np.array(
            item["params_point_xyz_vector_ijk_radii_m"],
            dtype=float,
        )
        for item in mate["entities"]
    ]
    direction = first[3:6] / np.linalg.norm(first[3:6])

    if np.linalg.norm(
        np.cross(second[:3] - first[:3], direction)
    ) > 1e-6:
        raise ValueError(f"Misaligned centres in {name}")

    points[index] = cad_to_ros @ first[:3]
    axes[index] = cad_to_ros @ direction

names = ["Base", "Hip", "Arm", "Forearm",
         "Wrist_B", "Wrist_A", "EE"]
shapes = {}

with zipfile.ZipFile(archive) as source:
    for name in names:
        matches = [
            key for key in components
            if key.endswith("_" + name + "-1")
        ]
        if len(matches) != 1:
            raise ValueError(f"Cannot identify component: {name}")

        raw = np.array(
            components[matches[0]]["transform_raw"],
            dtype=float,
        )
        rotation = raw[:9].reshape(3, 3).T

        if not np.allclose(
            rotation.T @ rotation, np.eye(3), atol=1e-7
        ) or not np.isclose(np.linalg.det(rotation), 1):
            raise ValueError(f"Invalid rotation: {name}")

        if not np.isclose(raw[12], 1):
            raise ValueError(f"Unsupported component scale: {name}")

        triangles = read_stl(source.read(name + ".STL")) / 1000
        shapes[name] = (
            triangles @ rotation.T + raw[9:12]
        ) @ cad_to_ros.T

base_origin = points[1].copy()
base_origin[2] = shapes["Base"][:, :, 2].min()

origins = {
    "Base": base_origin,
    "Hip": points[1],
    "Arm": points[2],
    "Forearm": points[3],
    "Wrist_B": points[4],
    "Wrist_A": points[5],
    "EE": points[6],
}

metadata = {"units": "metre", "links": {}, "joints": []}

for name in names:
    triangles = shapes[name] - origins[name]
    write_stl(
        package / "meshes/visual" / (name + ".stl"),
        triangles,
    )

    cloud = np.unique(triangles.reshape(-1, 3), axis=0)
    hull = ConvexHull(cloud)
    collision = cloud[hull.simplices].copy()

    normals = np.cross(
        collision[:, 1] - collision[:, 0],
        collision[:, 2] - collision[:, 0],
    )
    reverse = np.sum(
        normals * hull.equations[:, :3], axis=1
    ) < 0
    collision[reverse] = collision[reverse][:, [0, 2, 1]]

    write_stl(
        package / "meshes/collision" / (name + ".stl"),
        collision,
    )

    low, high = cloud.min(0), cloud.max(0)
    size = high - low
    metadata["links"][name] = {
        "origin_from_base_m": (
            origins[name] - base_origin
        ).tolist(),
        "provisional_mass_kg": 1.0,
        "provisional_com_m": ((low + high) / 2).tolist(),
        "provisional_box_inertia": [
            (size[1]**2 + size[2]**2) / 12,
            (size[0]**2 + size[2]**2) / 12,
            (size[0]**2 + size[1]**2) / 12,
        ],
    }

    print(
        f"{name}: {len(triangles)} visual triangles, "
        f"{len(collision)} collision triangles",
        flush=True,
    )

chain = [
    ("tower_joint", "Base", "Hip", 1, "revolute"),
    ("shoulder_joint", "Hip", "Arm", 2, "revolute"),
    ("elbow_joint", "Arm", "Forearm", 3, "revolute"),
    ("wrist_mount_joint", "Forearm", "Wrist_B", 4, "fixed"),
    ("wrist_pitch_joint", "Wrist_B", "Wrist_A", 5, "revolute"),
    ("wrist_roll_joint", "Wrist_A", "EE", 6, "revolute"),
]

for name, parent, child, index, kind in chain:
    metadata["joints"].append({
        "name": name,
        "parent": parent,
        "child": child,
        "type": kind,
        "origin_m": (origins[child] - origins[parent]).tolist(),
        "axis": axes[index].tolist(),
    })

(package / "config").mkdir(exist_ok=True)
(package / "config/cad_geometry.json").write_text(
    json.dumps(metadata, indent=2) + "\n"
)

print("\nDONE: seven visual meshes and seven collision meshes.")
print("Mass and inertia values are placeholders.")
