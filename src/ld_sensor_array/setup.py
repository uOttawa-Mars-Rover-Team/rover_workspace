from setuptools import find_packages, setup

package_name = "ld_sensor_array"

setup(
    name=package_name,
    version="0.0.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="raghavbh",
    maintainer_email="rbhar017@uottawa.ca",
    description="TODO: Package description",
    license="Apache-2.0",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "sensor_array_interface = ld_sensor_array.sensor_array_interface:main",
            "sensor_array_viewer = ld_sensor_array.sensor_array_viewer:main",
            "geiger_publisher = ld_sensor_array.geiger_publisher:main",
        ],
    },
)
