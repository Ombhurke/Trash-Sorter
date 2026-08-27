"""
High-Precision AI Waste Classifier (YOLOv8 + Spatial Target Zone + Pixel Contour Tracing).
Strictly classifies only genuine waste materials: Plastic, Paper, Cardboard, Glass, and Metal.
Traces pixel-level geometric contours and silhouettes around any object shape (circular, curved, spherical, or irregular).
Explicitly filters out humans, faces, room backgrounds, furniture, and office electronics.
"""

import os
import logging
from typing import Dict, Any, Optional, Tuple, List
import numpy as np
import cv2

# Canonical mapping of COCO classes to exact Waste Categories
YOLO_COCO_CATEGORY_MAP = {
    # PLASTIC WASTE (Code: 'P' -> Right Bin Blue)
    "bottle": "plastic",
    "plastic bottle": "plastic",
    "cup": "plastic",
    "plastic cup": "plastic",
    "toothbrush": "plastic",
    "plastic bag": "plastic",

    # PAPER WASTE (Code: 'A' -> Far Right Bin Green)
    "book": "paper",
    "paper": "paper",
    "newspaper": "paper",
    "magazine": "paper",
    "notebook": "paper",
    "document": "paper",

    # CARDBOARD WASTE (Code: 'C' -> Back Bin Brown)
    "box": "cardboard",
    "cardboard": "cardboard",
    "package": "cardboard",
    "carton": "cardboard",
    "shipping box": "cardboard",
    "suitcase": "cardboard",

    # GLASS WASTE (Code: 'G' -> Left Bin Gray)
    "wine glass": "glass",
    "glass": "glass",
    "vase": "glass",
    "bowl": "glass",
    "glass bottle": "glass",
    "jar": "glass",
    "glass jar": "glass",

    # METAL WASTE (Code: 'M' -> Far Left Bin Yellow)
    "can": "metal",
    "tin can": "metal",
    "soda can": "metal",
    "scissors": "metal",
    "knife": "metal",
    "fork": "metal",
    "spoon": "metal"
}

# Classes to strictly ignore (never classify as trash)
IGNORED_COCO_CLASSES = {
    "person", "face", "chair", "couch", "bed", "dining table", "tv", "monitor",
    "laptop", "mouse", "remote", "keyboard", "cell phone", "microwave", "oven",
    "toaster", "sink", "refrigerator", "clock", "bench", "bicycle", "car",
    "motorcycle", "airplane", "bus", "train", "truck", "boat", "traffic light",
    "fire hydrant", "stop sign", "potted plant", "backpack", "umbrella", "handbag",
    "tie", "suitcase", "frisbee", "skis", "snowboard", "sports ball", "kite",
    "baseball bat", "baseball glove", "skateboard", "surfboard", "tennis racket",
    "banana", "apple", "sandwich", "orange", "broccoli", "carrot", "hot dog",
    "pizza", "donut", "cake", "toilet", "teddy bear", "hair drier",
    "cat", "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe"
}


class OptimizedWasteClassifier:
    """
    High-Precision Waste Classifier with pixel-level organic shape contour tracing.
    """

    def __init__(
        self,
        model_name: str = "yolov8n.pt",
        confidence_threshold: float = 0.40,
        device: str = "auto"
    ):
        self.logger = logging.getLogger("WasteClassifier")
        self.confidence_threshold = confidence_threshold
        self.keys = ["plastic", "paper", "cardboard", "glass", "metal"]
        self.yolo_model = None
        self.torch_device = "cpu"

        # Resolve model absolute path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        backend_dir = os.path.dirname(os.path.dirname(current_dir))
        root_dir = os.path.dirname(backend_dir)
        
        candidates = [
            os.path.join(root_dir, model_name),
            os.path.join(backend_dir, model_name),
            model_name
        ]
        resolved_model_path = next((p for p in candidates if os.path.exists(p)), model_name)

        # 1. Initialize PyTorch device
        try:
            import torch
            if device == "auto":
                self.torch_device = "cuda" if torch.cuda.is_available() else "cpu"
            else:
                self.torch_device = device
        except Exception:
            self.torch_device = "cpu"

        # 2. Load Prebuilt YOLOv8 Model
        try:
            from ultralytics import YOLO
            self.logger.info(f"Loading YOLOv8 Model from '{resolved_model_path}' on {self.torch_device}...")
            self.yolo_model = YOLO(resolved_model_path)
            # Warm up with dummy inference pass to eliminate cold-start lag
            dummy_img = np.zeros((320, 320, 3), dtype=np.uint8)
            self.yolo_model(dummy_img, verbose=False)
            self.logger.info("YOLOv8 Model loaded and warmed up successfully.")
        except Exception as e:
            self.logger.warning(f"Could not load YOLOv8 ({e}).")
            self.yolo_model = None

    @property
    def model_type(self) -> str:
        if self.yolo_model is not None:
            return "ultralytics"
        return "heuristic"

    def analyze_frame(
        self,
        frame_bgr: np.ndarray,
        roi_bounds: Optional[Tuple[int, int, int, int]] = None
    ) -> Dict[str, Any]:
        """
        High-Accuracy Multi-Stage Inference:
        1. Runs YOLO on frame to locate objects.
        2. Filters out people, faces, backgrounds, office electronics.
        3. Validates that candidate trash item is placed INSIDE the central Target Zone.
        4. Traces exact organic/geometric contours (circles, curves, irregular shapes).
        5. If nothing is in Target Zone, returns is_valid=False (ZERO false positives).
        """
        if frame_bgr is None or frame_bgr.size == 0:
            return self._empty_result()

        h, w, _ = frame_bgr.shape
        if h < 40 or w < 40:
            return self._empty_result()

        if roi_bounds:
            rx1, ry1, rx2, ry2 = roi_bounds
        else:
            roi_size = min(w, h) // 2
            rx1, ry1 = (w - roi_size) // 2, (h - roi_size) // 2
            rx2, ry2 = rx1 + roi_size, ry1 + roi_size

        # --- Stage 1: Full-Frame YOLO Object Detection ---
        if self.yolo_model is not None:
            try:
                detection = self._run_yolo_detection(frame_bgr, rx1, ry1, rx2, ry2)
                if detection:
                    cat, raw_label, conf, bx1, by1, bx2, by2, contour = detection
                    probs = {k: (conf if k == cat else round((1.0 - conf) / 4.0, 3)) for k in self.keys}
                    return {
                        "probabilities": probs,
                        "best_category": cat,
                        "best_prob": conf,
                        "raw_label": raw_label,
                        "bbox": (bx1, by1, bx2, by2),
                        "contour": contour,
                        "is_valid": True
                    }
            except Exception as err:
                self.logger.error(f"YOLO detection error: {err}")

        # If no valid trash item in Target Zone, strictly return is_valid=False
        return self._empty_result()

    def _empty_result(self) -> Dict[str, Any]:
        return {
            "probabilities": {k: 0.0 for k in self.keys},
            "best_category": None,
            "best_prob": 0.0,
            "raw_label": "Target Zone Empty",
            "bbox": None,
            "contour": None,
            "is_valid": False
        }

    def _run_yolo_detection(
        self,
        frame_bgr: np.ndarray,
        rx1: int,
        ry1: int,
        rx2: int,
        ry2: int
    ) -> Optional[Tuple[str, str, float, int, int, int, int, Optional[np.ndarray]]]:
        """
        Runs YOLO and finds genuine waste items positioned in or intersecting the Target Zone.
        Extracts pixel-level geometric contours for the candidate item.
        """
        results = self.yolo_model(frame_bgr, verbose=False)
        best_candidate = None
        highest_score = 0.0

        target_cx = (rx1 + rx2) / 2.0
        target_cy = (ry1 + ry2) / 2.0
        roi_area = max(1, (rx2 - rx1) * (ry2 - ry1))

        for r in results:
            boxes = r.boxes
            for box in boxes:
                cls_id = int(box.cls[0])
                conf = float(box.conf[0])
                class_name = self.yolo_model.names.get(cls_id, "").lower()

                # Skip non-trash objects (humans, furniture, electronics)
                if class_name in IGNORED_COCO_CLASSES:
                    continue

                category = YOLO_COCO_CATEGORY_MAP.get(class_name, None)
                if not category:
                    continue

                # Bounding box coords
                bx1, by1, bx2, by2 = [int(v) for v in box.xyxy[0]]
                obj_cx = (bx1 + bx2) / 2.0
                obj_cy = (by1 + by2) / 2.0
                obj_area = max(1, (bx2 - bx1) * (by2 - by1))

                # Compute intersection with central Target Zone
                ix1, iy1 = max(rx1, bx1), max(ry1, by1)
                ix2, iy2 = min(rx2, bx2), min(ry2, by2)
                inter_area = max(0, ix2 - ix1) * max(0, iy2 - iy1)

                # Check if object center is inside or close to ROI
                center_in_roi = (rx1 - 30 <= obj_cx <= rx2 + 30) and (ry1 - 30 <= obj_cy <= ry2 + 30)
                overlap_ratio = inter_area / float(obj_area)
                roi_overlap_ratio = inter_area / float(roi_area)

                # Must be located in the Target Zone (at least 20% overlap or center inside ROI)
                if not (center_in_roi or overlap_ratio > 0.20 or roi_overlap_ratio > 0.15):
                    continue

                # Texture / Color Refinement for Bottle / Cup / Box
                final_cat = category
                crop = frame_bgr[max(0, by1):min(frame_bgr.shape[0], by2), max(0, bx1):min(frame_bgr.shape[1], bx2)]
                if crop.size > 0:
                    final_cat = self._refine_category(class_name, category, crop)

                score = conf * (1.0 + overlap_ratio * 0.5)

                if conf >= self.confidence_threshold and score > highest_score:
                    highest_score = score
                    label = f"{final_cat.capitalize()} ({class_name})"
                    contour = self._extract_object_contour(frame_bgr, bx1, by1, bx2, by2)
                    best_candidate = (final_cat, label, min(0.99, conf), bx1, by1, bx2, by2, contour)

        return best_candidate

    def _extract_object_contour(self, frame_bgr: np.ndarray, bx1: int, by1: int, bx2: int, by2: int) -> Optional[np.ndarray]:
        """
        Extracts pixel-level geometric outline/contour (circles, cylinders, irregular shapes)
        around the object within its bounding box region.
        """
        try:
            h, w = frame_bgr.shape[:2]
            pad = 2
            cbx1, cby1 = max(0, bx1 - pad), max(0, by1 - pad)
            cbx2, cby2 = min(w, bx2 + pad), min(h, by2 + pad)
            crop = frame_bgr[cby1:cby2, cbx1:cbx2]
            if crop.size == 0 or crop.shape[0] < 12 or crop.shape[1] < 12:
                return None

            gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)

            # Canny edge map & morphological closing
            edges = cv2.Canny(blurred, 30, 100)
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
            closed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel, iterations=2)

            contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
            if not contours:
                _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

            if contours:
                largest = max(contours, key=cv2.contourArea)
                area = cv2.contourArea(largest)
                crop_area = crop.shape[0] * crop.shape[1]

                if area > 0.08 * crop_area:
                    # Smooth polygon to follow curves / circles gracefully
                    epsilon = 0.007 * cv2.arcLength(largest, True)
                    approx = cv2.approxPolyDP(largest, epsilon, True)
                    contour_full = approx + np.array([cbx1, cby1])
                    return contour_full

            # Fallback polygon around bounding box
            return np.array([
                [[bx1, by1]], [[bx2, by1]], [[bx2, by2]], [[bx1, by2]]
            ], dtype=np.int32)
        except Exception:
            return None

    def _refine_category(self, class_name: str, base_cat: str, crop_bgr: np.ndarray) -> str:
        """Fine-grained visual texture disambiguation."""
        try:
            gray = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2GRAY)
            hsv = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2HSV)
            
            # Cardboard vs Paper: Check Brown Hue
            if base_cat in ["paper", "cardboard"] or class_name in ["box", "book"]:
                lower_brown = np.array([10, 40, 40], dtype=np.uint8)
                upper_brown = np.array([26, 255, 210], dtype=np.uint8)
                brown_ratio = float(np.sum(cv2.inRange(hsv, lower_brown, upper_brown) > 0)) / float(gray.size)
                if brown_ratio > 0.20:
                    return "cardboard"
                else:
                    return "paper" if class_name == "book" else base_cat

            # Bottle / Cup: Plastic vs Glass vs Metal
            if class_name in ["bottle", "cup"]:
                glare_ratio = float(np.sum(gray > 240)) / float(gray.size)
                mean_saturation = float(np.mean(hsv[:, :, 1]))
                # High specular glare with low saturation indicates metal can or clear glass
                if glare_ratio > 0.06 and mean_saturation < 50:
                    return "metal"
                elif mean_saturation < 30:
                    return "glass"
                return "plastic"

            return base_cat
        except Exception:
            return base_cat
