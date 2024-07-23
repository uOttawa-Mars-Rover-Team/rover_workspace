from setuptools import find_packages, setup

package_name = 'ld_controls_ros2'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='raghav',
    maintainer_email='raghav@todo.todo',
    description='TODO: Package description',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
        	'LD_GUI = ld_controls_ros2.LD_Temp_GUI:main',
            'MCU = ld_controls_ros2.MCU_interface_node:main'
        ],
    },
)
