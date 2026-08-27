import time
import logging
import threading
from typing import Callable, Dict, Optional
from backend.hardware.drivers.base_driver import BaseArmDriver

try:
    import serial
    import serial.tools.list_ports
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False

SERVO_PRESETS = {
    "P": {"base": 45, "shoulder": 60, "elbow": 90, "wrist": 120, "gripper": 70},
    "A": {"base": 70, "shoulder": 50, "elbow": 110, "wrist": 100, "gripper": 65},
    "C": {"base": 160, "shoulder": 65, "elbow": 85, "wrist": 130, "gripper": 75},
    "G": {"base": 135, "shoulder": 45, "elbow": 120, "wrist": 95, "gripper": 60},
    "M": {"base": 110, "shoulder": 55, "elbow": 95, "wrist": 115, "gripper": 80},
    "H": {"base": 90, "shoulder": 30, "elbow": 140, "wrist": 110, "gripper": 15},
    "E": {"base": 90, "shoulder": 90, "elbow": 90, "wrist": 90, "gripper": 0}
}

class ArduinoArmDriver(BaseArmDriver):
    """
    Physical PySerial Driver for Arduino UNO (`robotic_hand.ino`).
    Communicates at 19200 Baud with single-letter codes ('P', 'A', 'C', 'G', 'M', 'H', 'E').
    Listens for 'Done' signal on background reader thread.
    """
    
    def __init__(self, port: str = "COM3", baud_rate: int = 19200):
        self.port = port
        self.baud_rate = baud_rate
        self.connection = None
        self.reader_thread = None
        self.stop_event = threading.Event()
        self.done_callback: Optional[Callable[[], None]] = None
        
        self.current_angles = SERVO_PRESETS["H"].copy()
        self._connected = False

    def connect(self) -> bool:
        if not SERIAL_AVAILABLE:
            logging.warning("PySerial is not installed. Cannot initialize physical Arduino driver.")
            self._connected = False
            return False

        try:
            self.connection = serial.Serial(self.port, self.baud_rate, timeout=1)
            time.sleep(2.0)
            self._connected = True
            logging.info(f"[HARDWARE DRIVER] Connected to physical Arduino on {self.port} at {self.baud_rate} Baud.")
            
            self.stop_event.clear()
            self.reader_thread = threading.Thread(target=self._serial_read_loop, daemon=True)
            self.reader_thread.start()
            return True
        except Exception as e:
            logging.warning(f"[HARDWARE DRIVER] Failed to connect to physical serial port {self.port}: {e}")
            self._connected = False
            return False

    def disconnect(self):
        self.stop_event.set()
        if self.connection and self.connection.is_open:
            self.connection.close()
        self._connected = False
        logging.info("[HARDWARE DRIVER] Serial connection closed.")

    def is_connected(self) -> bool:
        return self._connected and self.connection is not None and self.connection.is_open

    def register_done_callback(self, callback: Callable[[], None]):
        self.done_callback = callback

    def get_servo_angles(self) -> Dict[str, float]:
        return self.current_angles.copy()

    def send_command(self, code: str) -> bool:
        if not code:
            return False

        code_upper = code.upper()
        valid_codes = ["P", "A", "C", "G", "M", "H", "E"]
        if code_upper not in valid_codes:
            logging.warning(f"[HARDWARE DRIVER] Invalid code '{code}'. Expected one of {valid_codes}")
            return False

        if code_upper in SERVO_PRESETS:
            self.current_angles = SERVO_PRESETS[code_upper].copy()

        if not self.is_connected():
            logging.warning(f"[HARDWARE DRIVER] Port {self.port} not connected. Cannot send command '{code_upper}'.")
            return False

        try:
            payload = code_upper.encode('utf-8')
            self.connection.write(payload)
            self.connection.flush()
            logging.info(f"[HARDWARE DRIVER] Transmitted code '{code_upper}' to Arduino on {self.port}.")
            return True
        except Exception as e:
            logging.error(f"[HARDWARE DRIVER] Failed to write code '{code_upper}' to Serial: {e}")
            return False

    def _serial_read_loop(self):
        while not self.stop_event.is_set() and self.connection and self.connection.is_open:
            try:
                line = self.connection.readline().decode('utf-8', errors='ignore').strip()
                if line:
                    logging.info(f"[ARDUINO SERIAL INPUT] -> {line}")
                    if "Done" in line or "Ready" in line:
                        logging.info("[HARDWARE DRIVER] Arduino emitted 'Done' movement signal.")
                        self.current_angles = SERVO_PRESETS["H"].copy()
                        if self.done_callback:
                            self.done_callback()
            except Exception as e:
                logging.error(f"[HARDWARE DRIVER] Error reading serial line: {e}")
                time.sleep(0.5)
