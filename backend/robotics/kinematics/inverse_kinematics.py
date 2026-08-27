"""
Analytical 6-DOF Inverse Kinematics (IK) Solver for Waste Segregation Robotic Arm.
Calculates servo joint angles (theta1..theta6 in degrees) dynamically for any 3D pose (X, Y, Z).
Zero hardcoded trajectories or predefined angles!
"""

from typing import Tuple, List, Optional
import numpy as np


class InverseKinematics:
    """
    Solves 6-DOF joint angles dynamically given target 3D Cartesian coordinates (X, Y, Z in mm).
    Link Dimensions (mm):
      - L1: Base to Shoulder (100 mm)
      - L2: Shoulder to Elbow (120 mm)
      - L3: Elbow to Wrist (130 mm)
      - L4: Wrist to End-Effector Gripper (150 mm)
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

    def solve_ik(
        self,
        target_xyz: Tuple[float, float, float],
        approach_pitch_deg: float = -45.0,
        wrist_roll_deg: float = 90.0,
        gripper_open: float = 0.5
    ) -> Tuple[List[float], bool]:
        """
        Solves joint angles dynamically for target 3D Cartesian position (x, y, z).
        
        Args:
            target_xyz: Target end-effector position (x, y, z) in mm.
            approach_pitch_deg: Desired end-effector pitch angle in degrees.
            wrist_roll_deg: Gripper roll angle in degrees.
            gripper_open: Gripper open state [0.0 = closed (15 deg), 1.0 = open (160 deg)].
            
        Returns:
            Tuple containing:
              - joint_angles_deg: List of 6 servo angles [theta1..theta6] in degrees.
              - is_reachable: Boolean flag indicating if target is within workspace reach.
        """
        x, y, z = target_xyz
        phi = np.radians(approach_pitch_deg)

        # 1. Base Joint Angle theta1
        theta1_rad = np.arctan2(y, x)
        theta1_deg = np.degrees(theta1_rad) + 90.0

        # Radial distance in horizontal XY plane
        r = np.sqrt(x**2 + y**2)

        # 2. Wrist Center Position (rw, zw)
        rw = r - self.L4 * np.cos(phi)
        zw = z - self.L1 - self.L4 * np.sin(phi)

        # Distance from shoulder to wrist center
        d_sq = rw**2 + zw**2
        d = np.sqrt(d_sq)

        # Workspace reachability check
        max_reach = self.L2 + self.L3
        min_reach = abs(self.L2 - self.L3)

        if d > max_reach or d < min_reach or d == 0:
            # Target is outside physical workspace reach; apply closest reachable boundary
            rw_clamped = rw * (max_reach * 0.98) / max(d, 1e-5)
            zw_clamped = zw * (max_reach * 0.98) / max(d, 1e-5)
            d_sq = rw_clamped**2 + zw_clamped**2
            rw, zw = rw_clamped, zw_clamped
            is_reachable = False
        else:
            is_reachable = True

        # 3. Law of Cosines for Elbow Angle theta3
        cos_theta3 = (d_sq - self.L2**2 - self.L3**2) / (2.0 * self.L2 * self.L3)
        cos_theta3 = float(np.clip(cos_theta3, -1.0, 1.0))
        theta3_rad = np.arccos(cos_theta3)
        theta3_deg = 180.0 - np.degrees(theta3_rad)

        # 4. Shoulder Angle theta2
        alpha = np.arctan2(zw, rw)
        beta = np.arctan2(self.L3 * np.sin(theta3_rad), self.L2 + self.L3 * np.cos(theta3_rad))
        theta2_rad = alpha + beta
        theta2_deg = np.degrees(theta2_rad) + 90.0

        # 5. Wrist Pitch Angle theta4
        theta4_rad = phi - (theta2_rad - np.pi / 2.0) - (np.pi - theta3_rad)
        theta4_deg = np.degrees(theta4_rad) + 90.0

        # 6. Gripper Servo Angle theta6 (15 deg = closed, 160 deg = open)
        theta6_deg = 15.0 + (160.0 - 15.0) * float(np.clip(gripper_open, 0.0, 1.0))

        # Clamp all servo angles to physical MG996R bounds [0, 180] degrees
        joint_angles = [
            float(np.clip(theta1_deg, 0.0, 180.0)),
            float(np.clip(theta2_deg, 0.0, 180.0)),
            float(np.clip(theta3_deg, 0.0, 180.0)),
            float(np.clip(theta4_deg, 0.0, 180.0)),
            float(np.clip(wrist_roll_deg, 0.0, 180.0)),
            float(np.clip(theta6_deg, 0.0, 180.0))
        ]

        return joint_angles, is_reachable
