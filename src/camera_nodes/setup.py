import os
import xml.etree.ElementTree as ET
from glob import glob

from setuptools import find_packages, setup

# Parse package info. from package.xml to prevent duplication of hardcoded
# info.
package_info = ET.parse("package.xml").getroot()
package_name = package_info.find("name").text
package_version = package_info.find("version").text
package_description = package_info.find("description").text
package_license = package_info.find("license").text
package_maintainers = ", ".join(
    [element.text for element in package_info.findall("maintainer")]
)
package_maintainer_emails = ", ".join(
    [element.attrib["email"] for element in package_info.findall("maintainer")]
)

setup(
    name=package_name,
    version=package_version,
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        (
            os.path.join("share", package_name, "launch"),
            glob(os.path.join("launch", "*launch.[pxy][yma]*")),
        ),
        ("share/" + package_name + "/config/", glob("config/*")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer=package_maintainers,
    maintainer_email=package_maintainer_emails,
    description=package_description,
    license=package_license,
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "picture = camera_nodes.picture:main",
            "panorama = camera_nodes.panorama:main",
            "video = camera_nodes.video:main",
            "aruco = camera_nodes.aruco:main",
            "controls = camera_nodes.camera_control_app:main",
            "publisher = camera_nodes.publisher:main",
            "qos_relay = camera_nodes.qos_relay:main",
            "rotation_control = camera_nodes.rotation_control:main",
        ],
    },
)
