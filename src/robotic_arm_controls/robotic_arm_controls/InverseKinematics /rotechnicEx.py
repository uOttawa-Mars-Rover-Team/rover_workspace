import ikpy.chain
import ikpy.utils.plot as plot_utils

import numpy as np
import time
import math

import matplotlib.pyplot
from mpl_toolkits.mplot3d import Axes3D

my_chain = ikpy.chain.Chain.from_urdf_file("rotechnicExURDF.urdf",active_links_mask=[False, True, True, True, True, True, True])

ax = matplotlib.pyplot.figure().add_subplot(111, projection='3d')


target_position = [ 0, 0,0.58]

target_orientation = [-1, 0, 0]



ik = my_chain.inverse_kinematics(target_position, target_orientation, orientation_mode="Y")
print("The angles of each joints are : ", list(map(lambda r:math.degrees(r),ik.tolist())))




computed_position = my_chain.forward_kinematics(ik)
print("Computed position: %s, original position : %s" % (computed_position[:3, 3], target_position))
print("Computed position (readable) : %s" % [ '%.2f' % elem for elem in computed_position[:3, 3] ])

my_chain.plot(ik, ax)

matplotlib.pyplot.show()
