"""
Hand-Eye Calibration & Coordinate Frame Transformation Module.
Computes the 4x4 Homogeneous Transformation Matrix T_cam_to_robot to map 3D points from
Camera Frame (X_c, Y_c, Z_c) into Robot Base Frame (X_r, Y_r, Z_r).
"""

from typing import Tuple, Optional, List
import numpy as np


class HandEyeCalibrator:
    """
    Manages spatial coordinate frame transformations between Camera and Robot Base frames.
    
    Transformation Equation:
      P_robot = T_cam_to_robot * P_camera
    where T_cam_to_robot is a 4x4 rigid body transformation matrix [R | t].
    """

    def __init__(self, transform_matrix: Optional[np.ndarray] = None):
        if transform_matrix is not None:
            self.T_cam_to_robot = transform_matrix
        else:
            self.T_cam_to_robot = np.array([
                [1.0,  0.0,  0.0,   0.0],
                [0.0, -1.0,  0.0, 350.0],
                [0.0,  0.0, -1.0, 450.0],
                [0.0,  0.0,  0.0,   1.0]
            ], dtype=np.float64)

    def set_calibration_matrix(self, R: np.ndarray, t: np.ndarray) -> None:
        T = np.eye(4, dtype=np.float64)
        T[0:3, 0:3] = R
        T[0:3, 3] = t.flatten()
        self.T_cam_to_robot = T

    def camera_to_robot_frame(self, camera_point: Tuple[float, float, float]) -> Tuple[float, float, float]:
        P_cam_homo = np.array([camera_point[0], camera_point[1], camera_point[2], 1.0], dtype=np.float64)
        P_robot_homo = self.T_cam_to_robot @ P_cam_homo
        return float(P_robot_homo[0]), float(P_robot_homo[1]), float(P_robot_homo[2])

    def robot_to_camera_frame(self, robot_point: Tuple[float, float, float]) -> Tuple[float, float, float]:
        T_inv = np.linalg.inv(self.T_cam_to_robot)
        P_rob_homo = np.array([robot_point[0], robot_point[1], robot_point[2], 1.0], dtype=np.float64)
        P_cam_homo = T_inv @ P_rob_homo
        return float(P_cam_homo[0]), float(P_cam_homo[1]), float(P_cam_homo[2])
