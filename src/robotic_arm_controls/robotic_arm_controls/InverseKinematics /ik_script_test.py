import math

def inverse_kinematics_3dof(x, y, z):
    # Set your link lengths (meters)
    a1 = 0.111  # base to shoulder (vertical offset)
    a2 = 0.53   # L3 length (shoulder to elbow)
    a3 = 0.3    # L4 length (elbow to wrist/end-effector)
    
    # Step 1: Base rotation
    theta1 = math.atan2(y, x)
    
    # Step 2: Distance from base joint to projection of end effector in plane
    r = math.sqrt(x**2 + y**2)

    # Step 3: Effective vertical distance from shoulder to target
    z_eff = z - a1
    
    # Step 4: Law of cosines for elbow
    D = (r**2 + z_eff**2 - a2**2 - a3**2) / (2 * a2 * a3)
    if abs(D) > 1:
        raise ValueError("Target out of reach")
    theta3 = math.atan2(-math.sqrt(1 - D**2), D)  # "elbow down" solution
    
    # Step 5: Shoulder angle
    theta2 = math.atan2(z_eff, r) - math.atan2(a3 * math.sin(theta3), a2 + a3 * math.cos(theta3))
    
    return [theta1, theta2, theta3]

# Example: target (x, y, z) = (0.3, 0.3, 0.4)
angles = inverse_kinematics_3dof(0.3, 0.3, 0.4)
print("Joint Angles (radians):", angles)
print("Joint Angles (degrees):", [math.degrees(a) for a in angles])


#L1 L2 angle is - 36 deg - 35.97 deg




#Elbow is -101.60
#Shoulder is -79.72 