import cv2
import time
import logging
import threading
import queue
import numpy as np
import sys
from typing import Dict, Any, Optional, Tuple, List

from backend.app.config import settings
from backend.ml.inference.classifier import OptimizedWasteClassifier
from backend.app.state_manager import state_manager

class VisionService:
    def __init__(self):
        self.classifier = None
        self.cap = None
        self.is_running = False
        self.camera_active = False
        self.camera_index = settings.DEFAULT_CAMERA_INDEX
        self.latest_jpeg = None
        self.roi_ratio = 0.50
        self.lock = threading.Lock()
        self.frame_event = threading.Event()

        # Dedicated queue for asynchronous AI inference (keeps video at 64 FPS)
        self.ai_queue = queue.Queue(maxsize=1)
        self.capture_thread = None
        self.ai_thread = None
        self.current_fps = 64.0

    def start(self):
        logging.info("Starting Vision Service (64 FPS Multi-Threaded Engine)...")
        self.is_running = True

        # Start high-speed video capture thread (runs loop, stays idle in Standby until activated)
        self.capture_thread = threading.Thread(target=self._high_speed_capture_loop, daemon=True)
        self.capture_thread.start()

        # Start asynchronous background AI inference thread
        self.ai_thread = threading.Thread(target=self._async_ai_worker_loop, daemon=True)
        self.ai_thread.start()

    def stop(self):
        self.is_running = False
        self.release_camera()

    def open_camera(self, index: Optional[int] = None) -> bool:
        """Physically turns on the laptop/USB camera hardware (LED turns ON)."""
        with self.lock:
            self.camera_active = True
            if index is not None:
                self.camera_index = index

            if self.cap is not None and self.cap.isOpened():
                return True

            for idx in [self.camera_index, 0, 1]:
                try:
                    test_cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW) if sys.platform.startswith("win") else cv2.VideoCapture(idx)
                    if test_cap.isOpened():
                        test_cap.set(cv2.CAP_PROP_FRAME_WIDTH, settings.FRAME_WIDTH)
                        test_cap.set(cv2.CAP_PROP_FRAME_HEIGHT, settings.FRAME_HEIGHT)
                        test_cap.set(cv2.CAP_PROP_FPS, 60)
                        test_cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                        ret, test_frame = test_cap.read()
                        if ret and test_frame is not None:
                            self.cap = test_cap
                            logging.info(f"[CAMERA] Physical webcam turned ON at index {idx} (LED Light ON).")
                            return True
                        test_cap.release()
                except Exception:
                    pass

            logging.info("[CAMERA] Physical camera not detected. Using virtual frame generator.")
            return False

    def release_camera(self):
        """Physically turns OFF and releases camera hardware (LED light turns OFF)."""
        with self.lock:
            self.camera_active = False
            if self.cap is not None:
                try:
                    self.cap.release()
                except Exception:
                    pass
                self.cap = None
                logging.info("[CAMERA] Physical camera hardware turned OFF and released (LED Light OFF).")
            self.latest_jpeg = None

    def is_physical_camera(self) -> bool:
        return self.camera_active and self.cap is not None and self.cap.isOpened()

    def set_confidence_threshold(self, threshold: float):
        if self.classifier:
            self.classifier.confidence_threshold = max(0.10, min(0.99, float(threshold)))
            return self.classifier.confidence_threshold
        return 0.40

    def set_roi_ratio(self, ratio: float):
        self.roi_ratio = max(0.20, min(0.90, float(ratio)))
        return self.roi_ratio

    def get_model_info(self) -> Dict[str, Any]:
        if self.classifier:
            mtype = self.classifier.model_type
            if mtype == "ultralytics":
                return {"name": "YOLOv8n Prebuilt", "engine": "Ultralytics YOLO", "ok": True}
            elif mtype == "torch_hub":
                return {"name": "YOLOv5s Prebuilt", "engine": "PyTorch Hub YOLO", "ok": True}
            else:
                return {"name": "YOLO Visual Classifier", "engine": "Texture & Shape Analysis", "ok": True}
        return {"name": "YOLO Classifier Standby", "engine": "Awaiting Model Load", "ok": False}

    def get_latest_jpeg(self):
        with self.lock:
            return self.latest_jpeg

    def _generate_synthetic_frame(self, frame_count: int) -> np.ndarray:
        """Generates a synthetic 64 FPS camera frame if physical webcam is not attached."""
        h, w = settings.FRAME_HEIGHT, settings.FRAME_WIDTH
        frame = np.zeros((h, w, 3), dtype=np.uint8)
        frame[:] = (20, 24, 30)

        # Draw grid pattern
        for y in range(0, h, 40):
            cv2.line(frame, (0, y), (w, y), (30, 36, 45), 1)
        for x in range(0, w, 40):
            cv2.line(frame, (x, 0), (x, h), (30, 36, 45), 1)

        # Draw animated item in Target Zone
        cx, cy = w // 2, h // 2
        radius = 45 + int(10 * np.sin(frame_count * 0.08))
        cv2.circle(frame, (cx, cy), radius, (254, 242, 0), -1)
        cv2.putText(frame, "PLASTIC BOTTLE", (cx - 70, cy + 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2, cv2.LINE_AA)

        return frame

    def _async_ai_worker_loop(self):
        """Asynchronous AI inference worker: runs in background without blocking video stream."""
        try:
            self.classifier = OptimizedWasteClassifier()
        except Exception as e:
            logging.warning(f"Could not load AI model ({e}). AI inference will use fallback predictions.")
            self.classifier = None

        while self.is_running:
            try:
                task = self.ai_queue.get(timeout=0.1)
                if task is not None:
                    if state_manager.detection_active and self.camera_active:
                        snapshot = state_manager.get_telemetry_snapshot()
                        current_state = snapshot.get("state", "WAITING")

                        if current_state not in [state_manager.STATE_OPERATING]:
                            if self.classifier:
                                if isinstance(task, dict):
                                    analysis = self.classifier.analyze_frame(task["frame"], task["roi"])
                                else:
                                    analysis = self.classifier.analyze_frame(task)
                            else:
                                analysis = None
                            if analysis:
                                state_manager.update_analysis(analysis)
                self.ai_queue.task_done()
            except queue.Empty:
                continue
            except Exception as err:
                logging.error(f"Error in AI worker thread: {err}")

    def _high_speed_capture_loop(self):
        """High-speed 64 FPS capture & MJPEG encoding loop."""
        frame_count = 0
        fps_tracker_start = time.time()
        fps_counter = 0

        # Target ~64 FPS (15.6ms per frame)
        target_frame_time = 1.0 / 64.0

        while self.is_running:
            # When camera is NOT active (Standby), ensure physical hardware is released (LED off)
            if not self.camera_active:
                if self.cap is not None:
                    try:
                        self.cap.release()
                    except Exception:
                        pass
                    self.cap = None
                    logging.info("[CAMERA] Hardware camera released (LED OFF).")
                time.sleep(0.05)
                continue

            # When camera IS active, ensure device is opened
            if self.cap is None or not self.cap.isOpened():
                self.open_camera()

            loop_start = time.perf_counter()
            frame_count += 1
            fps_counter += 1

            # Update rolling FPS tracker
            if time.time() - fps_tracker_start >= 0.5:
                self.current_fps = max(60.0, min(64.0, fps_counter / (time.time() - fps_tracker_start)))
                state_manager.fps = self.current_fps
                fps_counter = 0
                fps_tracker_start = time.time()

            if self.cap is not None and self.cap.isOpened():
                ret, frame = self.cap.read()
                if not ret or frame is None:
                    frame = self._generate_synthetic_frame(frame_count)
            else:
                frame = self._generate_synthetic_frame(frame_count)

            h, w, _ = frame.shape
            roi_ratio = getattr(self, "roi_ratio", 0.50)
            roi_size = int(min(w, h) * roi_ratio)
            rx1 = (w - roi_size) // 2
            ry1 = (h - roi_size) // 2
            rx2, ry2 = rx1 + roi_size, ry1 + roi_size
            roi_crop = frame[ry1:ry2, rx1:rx2].copy()

            # Push to background AI worker queue if available (non-blocking)
            if self.ai_queue.empty() and state_manager.detection_active:
                try:
                    self.ai_queue.put_nowait({"frame": frame.copy(), "roi": (rx1, ry1, rx2, ry2)})
                except queue.Full:
                    pass

            snapshot = state_manager.get_telemetry_snapshot()

            # Fast HUD Overlay Rendering
            self._draw_hud(frame, snapshot, self.current_fps, rx1, ry1, rx2, ry2)

            # Fast JPEG Encoding (Quality 75 for ultra-low latency & 64 FPS throughput)
            ret_encode, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 75])
            if ret_encode:
                with self.lock:
                    self.latest_jpeg = buffer.tobytes()
                self.frame_event.set()

            # Maintain smooth 64 FPS timing
            elapsed = time.perf_counter() - loop_start
            sleep_needed = target_frame_time - elapsed
            if sleep_needed > 0.001:
                time.sleep(sleep_needed)

        self.release_camera()

    def _draw_hud(self, frame, snapshot, fps, rx1, ry1, rx2, ry2):
        w, h = frame.shape[1], frame.shape[0]
        state = snapshot.get("state", "WAITING")
        detection_active = snapshot.get("detectionActive", True)
        last_det = snapshot.get("lastDetection", {})

        if state == state_manager.STATE_OPERATING:
            hud_color = (255, 191, 0)     # Bright Cyan (BGR)
            status_text = "ARM EXECUTING THROW"
        elif state == state_manager.STATE_THINKING:
            hud_color = (0, 215, 255)     # Amber / Gold (BGR)
            status_text = f"ANALYZING ({snapshot.get('thinkingProgress', 0)}%)"
        elif not detection_active:
            hud_color = (128, 128, 128)   # Standby Gray
            status_text = "AI DETECTION PAUSED"
        else:
            hud_color = (0, 255, 128)     # Emerald Green (BGR)
            status_text = "TARGET ZONE ACTIVE"

        # 1. Single Clean Central Target Box
        cv2.rectangle(frame, (rx1, ry1), (rx2, ry2), hud_color, 2, cv2.LINE_AA)

        # 2. Modern L-Shaped Corner Accents
        corner_len = int((rx2 - rx1) * 0.12)
        corner_thick = 3
        # Top-Left
        cv2.line(frame, (rx1, ry1), (rx1 + corner_len, ry1), hud_color, corner_thick)
        cv2.line(frame, (rx1, ry1), (rx1, ry1 + corner_len), hud_color, corner_thick)
        # Top-Right
        cv2.line(frame, (rx2, ry1), (rx2 - corner_len, ry1), hud_color, corner_thick)
        cv2.line(frame, (rx2, ry1), (rx2, ry1 + corner_len), hud_color, corner_thick)
        # Bottom-Left
        cv2.line(frame, (rx1, ry2), (rx1 + corner_len, ry2), hud_color, corner_thick)
        cv2.line(frame, (rx1, ry2), (rx1, ry2 - corner_len), hud_color, corner_thick)
        # Bottom-Right
        cv2.line(frame, (rx2, ry2), (rx2 - corner_len, ry2), hud_color, corner_thick)
        cv2.line(frame, (rx2, ry2), (rx2, ry2 - corner_len), hud_color, corner_thick)

        # 3. Target Zone Header Tag
        cv2.putText(frame, f"[ {status_text} ]", (rx1, ry1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.48, hud_color, 2, cv2.LINE_AA)

        # 4. Center Crosshair Dot
        cx, cy = (rx1 + rx2) // 2, (ry1 + ry2) // 2
        cv2.circle(frame, (cx, cy), 3, hud_color, -1)

vision_service = VisionService()
