import time
import logging
import threading
from typing import Callable, Dict, Any, Optional
from backend.app.hardware.base_driver import BaseArmDriver

SERVO_PRESETS = {
    "P": {"base": 45, "shoulder": 60, "elbow": 90, "wrist": 120, "gripper": 70},
    "A": {"base": 70, "shoulder": 50, "elbow": 110, "wrist": 100, "gripper": 65},
    "C": {"base": 160, "shoulder": 65, "elbow": 85, "wrist": 130, "gripper": 75},
    "G": {"base": 135, "shoulder": 45, "elbow": 120, "wrist": 95, "gripper": 60},
    "M": {"base": 110, "shoulder": 55, "elbow": 95, "wrist": 115, "gripper": 80},
    "H": {"base": 90, "shoulder": 30, "elbow": 140, "wrist": 110, "gripper": 15},
    "E": {"base": 90, "shoulder": 90, "elbow": 90, "wrist": 90, "gripper": 0}
}


class MockArmDriver(BaseArmDriver):
    """
    Simulation Driver for testing full-stack application without physical hardware.
    Smoothly interpolates virtual servo angles and triggers mechanical completion callbacks.
    """
    
    def __init__(self):
        self._connected = True
        self.done_callback: Optional[Callable[[], None]] = None
        self.current_angles = SERVO_PRESETS["H"].copy()
        self.target_angles = SERVO_PRESETS["H"].copy()
        self.animation_thread = None

    def connect(self) -> bool:
        self._connected = True
        logging.info("[MOCK DRIVER] Virtual Robotic Arm simulation active.")
        return True

    def disconnect(self):
        self._connected = False
        logging.info("[MOCK DRIVER] Virtual Robotic Arm disconnected.")

    def is_connected(self) -> bool:
        return False  # Return False for physical connection check so UI accurately reflects no physical hardware

    def get_hardware_status(self) -> Dict[str, Any]:
        return {
            "is_real_hardware": False,
            "connected": False,
            "port": "MOCK",
            "baud_rate": 19200,
            "label": "Arduino Hardware Disconnected",
            "detail": "Virtual Simulation Mode · No physical USB device connected",
            "ok": False
        }

    def register_done_callback(self, callback: Callable[[], None]):
        self.done_callback = callback

    def get_servo_angles(self) -> Dict[str, float]:
        return self.current_angles.copy()

    def send_command(self, code: str) -> bool:
        if not code:
            return False

        code_upper = code.upper()
        if code_upper not in SERVO_PRESETS:
            logging.warning(f"[MOCK DRIVER] Invalid command code '{code}'.")
            return False

        target = SERVO_PRESETS[code_upper]
        logging.info(f"[MOCK DRIVER] Command '{code_upper}' received. Moving virtual arm servos to {target}...")
        
        # Start background smooth trajectory interpolation
        threading.Thread(target=self._animate_movement, args=(target,), daemon=True).start()
        return True

    def _animate_movement(self, target_angles: Dict[str, float]):
        steps = 10
        delay = 0.1
        start_angles = self.current_angles.copy()

        for step in range(1, steps + 1):
            alpha = step / steps
            for joint in self.current_angles:
                self.current_angles[joint] = round(
                    start_angles[joint] + alpha * (target_angles[joint] - start_angles[joint]), 1
                )
            time.sleep(delay)

        # Hold target position briefly then return to home after 1.5 seconds
        time.sleep(1.5)
        
        # Interpolate back to home
        home_target = SERVO_PRESETS["H"]
        return_start = self.current_angles.copy()
        for step in range(1, steps + 1):
            alpha = step / steps
            for joint in self.current_angles:
                self.current_angles[joint] = round(
                    return_start[joint] + alpha * (home_target[joint] - return_start[joint]), 1
                )
            time.sleep(delay)

        logging.info("[MOCK DRIVER] Virtual arm completed movement cycle & returned Home.")
        if self.done_callback:
            try:
                self.done_callback()
            except Exception as e:
                logging.error(f"[MOCK DRIVER] Exception in done callback: {e}")
