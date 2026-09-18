import numpy as np
import serial

ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)  

def inverse_kinematics_3dof(target_pos, link_lengths):
    """
    Calculate the inverse kinematics for a 3DoF planar robot arm.

    Args:
        target_pos (tuple): The target position (x, y, z) for the end effector.
        link_lengths (tuple): The lengths of the three links (l1, l2, l3).

    Returns:
        tuple: The joint angles (theta1, theta2, theta3) in degrees.
    """
    x, y, z = target_pos
    l1, l2, l3 = link_lengths

    # Project the target onto the XY plane
    r = np.sqrt(x**2 + y**2)
    if r > (l1 + l2 + l3):
        raise ValueError("Target is out of reach")

    # Cosine law for theta2
    cos_theta2 = (r**2 - l1**2 - l2**2) / (2 * l1 * l2)
    if abs(cos_theta2) > 1:
        raise ValueError("Target is out of reach due to cosine law")
    theta2 = np.arccos(cos_theta2)

    # Sine law for theta1
    k1 = l1 + l2 * np.cos(theta2)
    k2 = l2 * np.sin(theta2)
    theta1 = np.arctan2(y, x) - np.arctan2(k2, k1)

    # Theta3: orientation of the end effector
    theta3 = np.arctan2(z, r) - (theta1 + theta2)

    # Convert to deg
    print(f"{np.degrees(theta1)};{np.degrees(theta2)};{np.degrees(theta3)}")

    return tuple(np.degrees([theta1, theta2, theta3]))
# Example usage
link_lengths = (500, 250, 330)  # Lengths of the robot arm links
target_pos = (1.5, 0.5, 0.2)    # Target position for the end effector

angles = inverse_kinematics_3dof(target_pos, link_lengths)

#ser.write(b'Hello, device!\n')  # Send data
print("Joint angles (degrees):", angles)


#L1 L2 angle is - 36 deg - 35.97 deg




