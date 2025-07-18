from ikpy.chain import Chain
from ikpy.link import OriginLink
import numpy as np
import os
import serial


import math
import matplotlib.pyplot
from mpl_toolkits.mplot3d import Axes3D
ax = matplotlib.pyplot.figure().add_subplot(111, projection='3d')

#ser = serial.Serial('/dev/ttyACM0', 115200, timeout=1)  

# Load the URDF file
urdf_path = "ikpytest.urdf"

# Create the kinematic chain from the URDF
robot_chain = Chain.from_urdf_file(
    urdf_path,
    base_elements=["base_footprint"],
    active_links_mask=[False, True, True, True, False]  # Only joints q2, q3, q4 are active
)

# Print the chain to verify
print("Kinematic Chain:")
for link in robot_chain.links:
    print(f"  {link.name}")

# Define the target position for the end-effector (in meters)
target_position = [0.2, 0, 0]  # x, y, z in world coordinates
initial_position = [0.0, 0.0, 0, 0.0, 0.0]  # Only indices 1,2,3 are active

# Compute the inverse kinema
# The result is a list of joint angles (including the fixed base joint)
ik_solution = robot_chain.inverse_kinematics(
    target_position=target_position,
    initial_position =initial_position, 
)

robot_chain.plot(ik_solution, ax)

# Print the IK solution
print("\nInverse Kinematics Solution (radians):")
for i, angle in enumerate(ik_solution):
    print(f"  Joint {i}: {math.degrees(angle):.2f}°")

out_string = f"{math.degrees(ik_solution[0]):.2f};{math.degrees(ik_solution[2]):.2f};{math.degrees(ik_solution[3]):.2f};{math.degrees(ik_solution[4]):.2f};"
#ser.write(out_string.encode())
print(out_string)
# Optionally, compute the forward kinematics to verify the result
end_effector_frame = robot_chain.forward_kinematics(ik_solution)
print("\nEnd-effector position from FK:")
print(f"  Position: {end_effector_frame[:3, 3]}")
#ser.close()


matplotlib.pyplot.show()
