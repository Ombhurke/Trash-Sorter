"""
Forward Kinematics (FK) Solver for 6-DOF Robotic Manipulator.
Computes 3D End-Effector Cartesian Position (X, Y, Z in mm) from Joint Angles.
"""

from typing import List, Tuple
import numpy as np


class ForwardKinematics:
    """
    Solves 6-DOF End-Effector position using Denavit-Hartenberg (D-H) link parameters.
    Link Dimensions (mm):
      - L1 (Base to Shoulder): 100.0 mm
      - L2 (Shoulder to Elbow): 120.0 mm
      - L3 (Elbow to Wrist): 130.0 mm
      - L4 (Wrist to End-Effector Gripper): 150.0 mm
    """

    def __init__(
        self,
        l1: float = 100.0,
        l2: float = 120.0,
        l3: float = 130.0,
        l4: float = 150.0
    ):
        self.L1 = l1
        self.L2 = l2
        self.L3 = l3
        self.L4 = l4

    def compute_fk(self, joint_angles_deg: List[float]) -> Tuple[float, float, float]:
        """
        Computes 3D End-Effector position (X, Y, Z) in mm given 6 joint angles in degrees.
        
        Args:
            joint_angles_deg: List of 6 joint angles [theta1, theta2, theta3, theta4, theta5, theta6].
            
        Returns:
            Tuple (x, y, z) in mm.
        """
        if len(joint_angles_deg) < 6:
            joint_angles_deg = list(joint_angles_deg) + [90.0] * (6 - len(joint_angles_deg))

        # Convert angles from degrees to radians and adjust servo zero offsets
        q1 = np.radians(joint_angles_deg[0] - 90.0)  # Base rotation
        q2 = np.radians(joint_angles_deg[1] - 90.0)  # Shoulder pitch
        q3 = np.radians(joint_angles_deg[2] - 90.0)  # Elbow pitch
        q4 = np.radians(joint_angles_deg[3] - 90.0)  # Wrist pitch

        # Radial reach R in 2D sagittal plane
        r = (self.L2 * np.cos(q2) +
             self.L3 * np.cos(q2 + q3) +
             self.L4 * np.cos(q2 + q3 + q4))

        # 3D Cartesian Position
        x = float(r * np.cos(q1))
        y = float(r * np.sin(q1))
        z = float(self.L1 +
                  self.L2 * np.sin(q2) +
                  self.L3 * np.sin(q2 + q3) +
                  self.L4 * np.sin(q2 + q3 + q4))

        return x, y, z
