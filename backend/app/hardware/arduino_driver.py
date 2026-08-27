import time
import logging
import threading
from typing import Callable, Dict, Any, Optional, List
from collections import deque
from backend.app.hardware.base_driver import BaseArmDriver

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
    "R": {"base": 90, "shoulder": 30, "elbow": 140, "wrist": 110, "gripper": 15},
    "E": {"base": 90, "shoulder": 90, "elbow": 90, "wrist": 90, "gripper": 0}
}

CODE_LABELS = {
    "P": "Plastic (Right Bin)",
    "A": "Paper (Far Right Bin)",
    "C": "Cardboard (Back Bin)",
    "G": "Glass (Left Bin)",
    "M": "Metal (Far Left Bin)",
    "H": "Home Position",
    "R": "Reset State",
    "E": "Emergency Stop"
}


class ArduinoArmDriver(BaseArmDriver):
    """
    Physical PySerial Driver for Arduino UNO (`robotic_arm_smooth_shoulder.ino`).
    Fast, non-blocking connection to specified COM port (e.g. COM10) with live Serial Monitor streaming.
    """

    def __init__(self, port: str = "COM10", baud_rate: int = 19200):
        self.port = port
        self.baud_rate = baud_rate
        self.connection = None
        self.reader_thread = None
        self.stop_event = threading.Event()
        self.op_lock = threading.RLock()
        self.done_callback: Optional[Callable[[], None]] = None
        self.log_callback: Optional[Callable[[], None]] = None

        self.current_angles = SERVO_PRESETS["H"].copy()
        self._connected = False
        self._detected_port: Optional[str] = None
        self._status_detail = "Ready to connect"

        # In-memory circular buffer for Serial Monitor logs (stores last 100 entries)
        self.serial_logs = deque(maxlen=100)
        self._add_log("INFO", f"Serial driver initialized for {self.port} @ {self.baud_rate} Baud.")

    def _add_log(self, direction: str, data: str):
        entry = {
            "timestamp": time.strftime("%H:%M:%S"),
            "direction": direction,  # "TX", "RX", "INFO", "ERROR"
            "data": data
        }
        self.serial_logs.append(entry)
        if self.log_callback:
            try:
                self.log_callback()
            except Exception:
                pass

    def get_serial_logs(self) -> List[Dict[str, str]]:
        return list(self.serial_logs)

    def clear_serial_logs(self):
        self.serial_logs.clear()
        self._add_log("INFO", "Serial Monitor log cleared.")

    def get_available_ports(self) -> List[str]:
        if not SERIAL_AVAILABLE:
            return []
        try:
            return [p.device for p in serial.tools.list_ports.comports()]
        except Exception:
            return []

    def get_available_ports_info(self) -> List[Dict[str, str]]:
        if not SERIAL_AVAILABLE:
            return []
        try:
            return [
                {
                    "port": p.device,
                    "description": p.description or p.device,
                    "hwid": p.hwid or ""
                }
                for p in serial.tools.list_ports.comports()
            ]
        except Exception:
            return []

    def connect(self, port: Optional[str] = None, baud_rate: Optional[int] = None) -> bool:
        with self.op_lock:
            if port:
                self.port = str(port).strip()
            if baud_rate:
                self.baud_rate = int(baud_rate)

            if not SERIAL_AVAILABLE:
                self._connected = False
                self._status_detail = "PySerial package not installed"
                self._add_log("ERROR", "PySerial package is missing. Install with 'pip install pyserial'.")
                return False

            target_port = self.port.strip()

            # If already connected to target_port, return True
            if self.is_connected() and self._detected_port == target_port:
                return True

            # Cleanly disconnect existing connection
            self._disconnect_internal()

            try:
                self._add_log("INFO", f"Opening serial port {target_port} at {self.baud_rate} Baud...")
                self.connection = serial.Serial(target_port, self.baud_rate, timeout=0.1, write_timeout=0.5)
                time.sleep(0.3)  # Brief delay for Arduino DTR reset

                self._connected = True
                self._detected_port = target_port
                self._status_detail = f"Connected on {target_port} · {self.baud_rate} Baud"
                logging.info(f"[HARDWARE] Arduino connected on {target_port} @ {self.baud_rate} Baud.")
                self._add_log("INFO", f"Successfully connected to Arduino on {target_port} @ {self.baud_rate} Baud.")

                # Flush stale buffer
                try:
                    self.connection.reset_input_buffer()
                    self.connection.reset_output_buffer()
                except Exception:
                    pass

                # Start reader thread to listen for Arduino serial monitor outputs
                self.stop_event.clear()
                self.reader_thread = threading.Thread(target=self._serial_read_loop, daemon=True)
                self.reader_thread.start()
                return True
            except Exception as e:
                self._connected = False
                self._detected_port = None
                self._status_detail = f"Failed to connect on {target_port}: {e}"
                self._add_log("ERROR", f"Failed to connect on {target_port}: {e}")
                logging.error(f"[HARDWARE] Connect error on {target_port}: {e}")
                return False

    def disconnect(self, silent: bool = False):
        with self.op_lock:
            self._disconnect_internal()
            if not silent:
                self._add_log("INFO", f"Disconnected from {self.port}.")

    def _disconnect_internal(self):
        self.stop_event.set()
        if self.connection:
            try:
                if self.connection.is_open:
                    self.connection.close()
            except Exception:
                pass
        self.connection = None
        self._connected = False
        self._detected_port = None
        self._status_detail = "Disconnected"

    def is_connected(self) -> bool:
        return self._connected and self.connection is not None and getattr(self.connection, "is_open", False)

    def get_hardware_status(self) -> Dict[str, Any]:
        connected = self.is_connected()
        ports = self.get_available_ports()

        if connected:
            label = "Arduino Uno Connected"
            detail = self._status_detail
            ok = True
        else:
            label = "Arduino Not Connected"
            if not ports:
                detail = f"No USB device found on {self.port}"
            else:
                detail = f"Port {self.port} offline (Available: {', '.join(ports)})"
            ok = False

        return {
            "is_real_hardware": True,
            "connected": connected,
            "port": self._detected_port or self.port,
            "baud_rate": self.baud_rate,
            "label": label,
            "detail": detail,
            "ok": ok,
            "available_ports": ports,
            "available_ports_info": self.get_available_ports_info(),
            "logs": self.get_serial_logs()
        }

    def register_done_callback(self, callback: Callable[[], None]):
        self.done_callback = callback

    def register_log_callback(self, callback: Callable[[], None]):
        self.log_callback = callback

    def get_servo_angles(self) -> Dict[str, float]:
        return self.current_angles.copy()

    def send_command(self, code: str) -> bool:
        if not code:
            return False

        code_upper = code.strip().upper()
        if not code_upper:
            return False

        # Set preset angles
        if code_upper in SERVO_PRESETS:
            self.current_angles = SERVO_PRESETS[code_upper].copy()

        label = CODE_LABELS.get(code_upper, f"Command '{code_upper}'")

        if not self.is_connected():
            logging.warning(f"[HARDWARE] Port {self.port} not connected. Command '{code_upper}' ({label}) simulated.")
            self._add_log("TX", f"'{code_upper}' -> {label} (Offline)")
            self._add_log("RX (Simulated)", f"{label.split('(')[0].strip()} Selected")
            # If not physically connected, trigger simulated done callback so state machine completes deterministically
            threading.Thread(target=self._simulate_done_fallback, args=(label,), daemon=True).start()
            return False

        try:
            payload = (code_upper + "\n").encode('utf-8')
            self.connection.write(payload)
            self.connection.flush()
            logging.info(f"[HARDWARE] Transmitted code '{code_upper}' to Arduino on {self._detected_port or self.port}.")
            self._add_log("TX", f"'{code_upper}' -> {label}")
            return True
        except Exception as e:
            logging.error(f"[HARDWARE] Serial write error for '{code_upper}': {e}")
            self._add_log("ERROR", f"Serial write failed: {e}")
            self.disconnect(silent=True)
            # Fallback completion so system does not lock up on write error
            threading.Thread(target=self._simulate_done_fallback, args=(label,), daemon=True).start()
            return False

    def _simulate_done_fallback(self, label: str):
        # Simulate arm throw trajectory timing (2.5 seconds)
        time.sleep(2.5)
        self.current_angles = SERVO_PRESETS["H"].copy()
        self._add_log("RX (Simulated)", "Done")
        if self.done_callback:
            try:
                self.done_callback()
            except Exception as e:
                logging.error(f"[HARDWARE] Exception in done callback: {e}")

    def _serial_read_loop(self):
        while not self.stop_event.is_set() and self.connection and getattr(self.connection, "is_open", False):
            try:
                raw = self.connection.readline()
                if raw:
                    line = raw.decode('utf-8', errors='ignore').strip()
                    if line:
                        logging.info(f"[ARDUINO SERIAL INPUT] -> {line}")
                        self._add_log("RX", line)
                        # "Done" signals movement routine completion from robotic_arm_smooth_shoulder.ino
                        if line == "Done" or "Done" in line:
                            logging.info("[HARDWARE] Arduino emitted 'Done' movement completion signal.")
                            self.current_angles = SERVO_PRESETS["H"].copy()
                            if self.done_callback:
                                try:
                                    self.done_callback()
                                except Exception as e:
                                    logging.error(f"[HARDWARE] Done callback execution error: {e}")
                        elif "Ready" in line:
                            logging.info("[HARDWARE] Arduino initialization ready.")
                            self.current_angles = SERVO_PRESETS["H"].copy()
            except Exception as e:
                if not self.stop_event.is_set():
                    logging.error(f"[HARDWARE] Serial read loop error: {e}")
                    self._add_log("ERROR", f"Serial read error: {e}")
                self._disconnect_internal()
                break
