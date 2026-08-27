"""
Object 3D Pose Estimator Module.
Estimates 3D spatial position (X, Y, Z in mm) and rotation angle of detected objects from 2D bounding boxes.
"""

from dataclasses import dataclass
from typing import Tuple, Optional
import numpy as np


@dataclass
class ObjectPose:
    """3D Pose container for detected waste items."""
    x_cam: float
    y_cam: float
    z_cam: float
    orientation_deg: float
    confidence: float


class ObjectPoseEstimator:
    """
    Estimates 3D camera coordinates (X_c, Y_c, Z_c) using pinhole camera intrinsic parameters.
    """

    def __init__(
        self,
        focal_length_px: float = 800.0,
        cx: float = 640.0,
        cy: float = 360.0,
        assumed_object_height_mm: float = 120.0
    ):
        self.fx = focal_length_px
        self.fy = focal_length_px
        self.cx = cx
        self.cy = cy
        self.assumed_height_mm = assumed_object_height_mm

    def estimate_pose(
        self,
        bbox: Tuple[int, int, int, int],
        confidence: float = 0.90,
        image_shape: Tuple[int, int] = (720, 1280)
    ) -> ObjectPose:
        """
        Estimates 3D pose from bounding box (x1, y1, x2, y2).
        """
        x1, y1, x2, y2 = bbox
        center_u = (x1 + x2) / 2.0
        center_v = (y1 + y2) / 2.0
        box_h_px = max(1.0, float(y2 - y1))

        z_cam = (self.fy * self.assumed_height_mm) / box_h_px
        z_cam = float(np.clip(z_cam, 200.0, 800.0))

        x_cam = (center_u - self.cx) * z_cam / self.fx
        y_cam = (center_v - self.cy) * z_cam / self.fy

        box_w_px = max(1.0, float(x2 - x1))
        orientation_deg = float(np.degrees(np.arctan2(box_h_px, box_w_px)))

        return ObjectPose(
            x_cam=x_cam,
            y_cam=y_cam,
            z_cam=z_cam,
            orientation_deg=orientation_deg,
            confidence=confidence
        )
