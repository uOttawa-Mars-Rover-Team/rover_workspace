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
package_url = package_info.find("url").text

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
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer=package_maintainers,
    maintainer_email=package_maintainer_emails,
    url=package_url,
    description=package_description,
    license=package_license,
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "keyboard_ik_controls = robotic_arm_controls.keyboard_ik_controls:main",
            "logitech_ik_controls = robotic_arm_controls.logitech_ik_controls:main",
            "logitech_ik_keyboard_controls = robotic_arm_controls.logitech_ik_keyboard_controls:main",
            "m_arm_controls = robotic_arm_controls.m_arm_controls:main",
            "old_manual = robotic_arm_controls.old_manual:main",
            "router = robotic_arm_controls.router:main",
            "spacemouse_ik_controls = robotic_arm_controls.spacemouse_ik_controls:main",
            "template_pub_sub = robotic_arm_controls.template_pub_sub:main",
            "toggler = robotic_arm_controls.toggler:main"
        ],
    },
)
