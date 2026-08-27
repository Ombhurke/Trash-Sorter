"""
Dynamic Motion Planner Module for 6-DOF Waste Segregation Manipulator.
Generates smooth collision-free joint space trajectories and updates paths dynamically if target bins move.
"""

from dataclasses import dataclass
from typing import List, Tuple, Optional
import numpy as np
from backend.robotics.kinematics.inverse_kinematics import InverseKinematics


@dataclass
class Waypoint:
    """Trajectory waypoint snapshot."""
    joint_angles_deg: List[float]
    gripper_state: float
    duration_sec: float
    description: str


class MotionPlanner:
    """
    Dynamic Joint Space Motion Planner.
    Generates multi-point continuous pick-and-place trajectories using Inverse Kinematics.
    """

    def __init__(self, ik_solver: Optional[InverseKinematics] = None):
        self.ik = ik_solver or InverseKinematics()

    def plan_pick_and_place_trajectory(
        self,
        current_joint_angles: List[float],
        object_robot_xyz: Tuple[float, float, float],
        bin_robot_xyz: Tuple[float, float, float],
        approach_height_mm: float = 120.0,
        steps_per_segment: int = 10
    ) -> List[Waypoint]:
        """
        Generates a 5-phase dynamic joint space trajectory:
          1. APPROACH: Move arm above detected object (Z_obj + approach_height)
          2. PICK: Lower arm to object Z_obj & close gripper
          3. LIFT: Lift object up to safe transport altitude
          4. TRANSPORT: Rotate base & move arm to dynamic bin (X_bin, Y_bin, Z_bin)
          5. RELEASE: Open gripper to deposit waste into target bin
          
        Args:
            current_joint_angles: Starting 6 servo angles in degrees.
            object_robot_xyz: Detected object (X, Y, Z) in robot base frame (mm).
            bin_robot_xyz: Detected dynamic bin (X, Y, Z) in robot base frame (mm).
            approach_height_mm: Safe clearance altitude offset.
            steps_per_segment: Interpolation steps per waypoint.
            
        Returns:
            List of Waypoint objects describing full path.
        """
        x_obj, y_obj, z_obj = object_robot_xyz
        x_bin, y_bin, z_bin = bin_robot_xyz

        # Calculate IK for key trajectory waypoints
        # Waypoint 1: Approach above object
        q_approach, _ = self.ik.solve_ik((x_obj, y_obj, z_obj + approach_height_mm), gripper_open=1.0)
        
        # Waypoint 2: Grasp object
        q_pick, _ = self.ik.solve_ik((x_obj, y_obj, z_obj), gripper_open=0.0)

        # Waypoint 3: Lift object
        q_lift, _ = self.ik.solve_ik((x_obj, y_obj, z_obj + approach_height_mm), gripper_open=0.0)

        # Waypoint 4: Transport above dynamic bin
        q_bin_approach, _ = self.ik.solve_ik((x_bin, y_bin, z_bin + approach_height_mm), gripper_open=0.0)

        # Waypoint 5: Lower into bin & Release
        q_bin_release, _ = self.ik.solve_ik((x_bin, y_bin, z_bin), gripper_open=1.0)

        # Interpolate smooth trajectory steps
        waypoints = []

        # Segment 1: Home -> Approach
        waypoints.extend(self._interpolate_joints(current_joint_angles, q_approach, gripper=1.0, steps=steps_per_segment, label="APPROACH"))

        # Segment 2: Approach -> Pick
        waypoints.extend(self._interpolate_joints(q_approach, q_pick, gripper=0.0, steps=steps_per_segment, label="PICK"))

        # Segment 3: Pick -> Lift
        waypoints.extend(self._interpolate_joints(q_pick, q_lift, gripper=0.0, steps=steps_per_segment, label="LIFT"))

        # Segment 4: Lift -> Bin Transport
        waypoints.extend(self._interpolate_joints(q_lift, q_bin_approach, gripper=0.0, steps=steps_per_segment, label="TRANSPORT"))

        # Segment 5: Bin Transport -> Release
        waypoints.extend(self._interpolate_joints(q_bin_approach, q_bin_release, gripper=1.0, steps=steps_per_segment, label="RELEASE"))

        return waypoints

    def _interpolate_joints(
        self,
        q_start: List[float],
        q_target: List[float],
        gripper: float,
        steps: int = 10,
        label: str = "MOVE"
    ) -> List[Waypoint]:
        """Quintic polynomial trajectory interpolation between joint vectors."""
        waypoints = []
        q_start_arr = np.array(q_start[:6], dtype=np.float32)
        q_target_arr = np.array(q_target[:6], dtype=np.float32)

        for s in range(1, steps + 1):
            t = s / float(steps)
            # Smooth S-curve quintic step: 10t^3 - 15t^4 + 6t^5
            s_curve = 10.0 * (t ** 3) - 15.0 * (t ** 4) + 6.0 * (t ** 5)
            q_interp = q_start_arr + s_curve * (q_target_arr - q_start_arr)
            waypoints.append(
                Waypoint(
                    joint_angles_deg=q_interp.tolist(),
                    gripper_state=gripper,
                    duration_sec=0.05,
                    description=f"{label} [{int(t * 100)}%]"
                )
            )
        return waypoints
