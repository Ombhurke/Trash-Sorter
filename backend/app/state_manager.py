import time
import logging
import threading
import json
from collections import defaultdict
from typing import List, Dict, Any
from fastapi import WebSocket

from backend.app.config import settings
from backend.app.hardware.factory import get_hardware_driver
from backend.app.database import log_detection, log_system_event, log_action, get_today_statistics

CODE_TO_CATEGORY = {
    "P": "PLASTIC",
    "A": "PAPER",
    "C": "CARDBOARD",
    "G": "GLASS",
    "M": "METAL"
}

CATEGORY_TO_CODE = {
    "PLASTIC": "P",
    "PAPER": "A",
    "CARDBOARD": "C",
    "GLASS": "G",
    "METAL": "M"
}

CATEGORY_LABELS = {
    "PLASTIC": "Plastic Bottle",
    "PAPER": "Paper Sheet",
    "CARDBOARD": "Cardboard Box",
    "GLASS": "Glass Jar",
    "METAL": "Metal Can"
}

SERVER_START_TIME = time.time()

class DashboardStateManager:
    STATE_WAITING = "WAITING"
    STATE_THINKING = "THINKING"
    STATE_OPERATING = "OPERATING"
    STATE_EMERGENCY = "EMERGENCY"

    MODE_AUTONOMOUS = "AUTONOMOUS"
    MODE_MANUAL = "MANUAL"

    def __init__(self):
        self.lock = threading.RLock()
        
        self.state = self.STATE_WAITING
        self.mode = self.MODE_AUTONOMOUS
        self.detection_active = False
        self.thinking_progress = 0
        self.thinking_duration = getattr(settings, "THINKING_DURATION", 5.0)
        self.fps = 29.8
        self.thinking_start_time = None
        self.accumulated_scores = defaultdict(float)
        self.sample_count = 0
        self.active_timer: Optional[threading.Timer] = None

        self.last_detection = {
            "id": "seed",
            "category": "PLASTIC",
            "label": "Plastic Bottle",
            "confidence": 98.6,
            "code": "P",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }

        self.active_websockets: List[WebSocket] = []
        self.loop = None

        # Instantiate isolated hardware driver (Mock or PySerial Arduino)
        self.hardware = get_hardware_driver(
            mode=settings.HARDWARE_MODE,
            port=settings.SERIAL_PORT,
            baud_rate=settings.BAUD_RATE
        )
        self.hardware.register_done_callback(self.handle_arm_done)
        if hasattr(self.hardware, "register_log_callback"):
            self.hardware.register_log_callback(self.broadcast_telemetry)

        log_system_event("INFO", "SYSTEM", f"State Manager initialized. Hardware mode: {settings.HARDWARE_MODE}")

    def set_event_loop(self, loop):
        self.loop = loop

    # --- WebSockets ---
    async def connect_ws(self, websocket: WebSocket):
        import asyncio
        self.loop = asyncio.get_running_loop()
        await websocket.accept()
        with self.lock:
            if websocket not in self.active_websockets:
                self.active_websockets.append(websocket)
        logging.info(f"[WEBSOCKET] Client connected. Total clients: {len(self.active_websockets)}")
        try:
            await websocket.send_text(json.dumps(self.get_telemetry_snapshot()))
        except Exception:
            pass

    def disconnect_ws(self, websocket: WebSocket):
        with self.lock:
            if websocket in self.active_websockets:
                self.active_websockets.remove(websocket)
        logging.info("[WEBSOCKET] Client disconnected.")

    def broadcast_telemetry(self):
        snapshot = self.get_telemetry_snapshot()
        message = json.dumps(snapshot)
        with self.lock:
            loop = self.loop
            if not loop or not loop.is_running():
                try:
                    import asyncio
                    loop = asyncio.get_event_loop()
                except Exception:
                    pass

            if loop and loop.is_running():
                for ws in list(self.active_websockets):
                    try:
                        import asyncio
                        async def _safe_send(target_ws=ws, payload=message):
                            try:
                                await target_ws.send_text(payload)
                            except Exception:
                                with self.lock:
                                    if target_ws in self.active_websockets:
                                        self.active_websockets.remove(target_ws)
                        asyncio.run_coroutine_threadsafe(_safe_send(), loop)
                    except Exception:
                        if ws in self.active_websockets:
                            self.active_websockets.remove(ws)

    # --- AI & Vision Inference Updates ---
    def set_detection_active(self, active: bool):
        with self.lock:
            self.detection_active = active
            if not active and self.state == self.STATE_THINKING:
                self.state = self.STATE_WAITING
                self.thinking_progress = 0
                self.accumulated_scores.clear()
        log_system_event("INFO", "VISION", f"Camera AI Detection {'Enabled' if active else 'Paused'}")
        self.broadcast_telemetry()
        return self.detection_active

    def toggle_detection(self):
        return self.set_detection_active(not self.detection_active)

    def update_analysis(self, analysis: Dict[str, Any]):
        with self.lock:
            if not self.detection_active:
                return

            if self.mode != self.MODE_AUTONOMOUS:
                return

            if self.state in [self.STATE_OPERATING, self.STATE_EMERGENCY]:
                return

            current_time = time.time()
            is_valid = analysis.get("is_valid", False) if analysis else False
            best_cat = analysis.get("best_category", None) if analysis else None

            if self.state == self.STATE_WAITING:
                if is_valid and best_cat:
                    self.state = self.STATE_THINKING
                    self.thinking_start_time = current_time
                    self.thinking_progress = 0
                    self.accumulated_scores.clear()
                    self.sample_count = 0
                    logging.info("[STATE MACHINE] Item detected. Entering THINKING state.")

            elif self.state == self.STATE_THINKING:
                if is_valid and analysis:
                    probs = analysis.get("probabilities", {})
                    for cat_key, prob in probs.items():
                        self.accumulated_scores[cat_key] += prob
                    self.sample_count += 1

                elapsed = current_time - self.thinking_start_time
                duration = getattr(self, "thinking_duration", settings.THINKING_DURATION)
                self.thinking_progress = min(100, int((elapsed / duration) * 100))

                if elapsed >= duration:
                    if self.sample_count > 0 and self.accumulated_scores:
                        final_cat_key = max(self.accumulated_scores, key=self.accumulated_scores.get)
                        avg_prob = self.accumulated_scores[final_cat_key] / self.sample_count

                        category_upper = final_cat_key.upper()
                        code = CATEGORY_TO_CODE.get(category_upper, "P")
                        label = CATEGORY_LABELS.get(category_upper, "Plastic Bottle")

                        self.last_detection = {
                            "id": f"det_{int(time.time()*1000)}",
                            "category": category_upper,
                            "label": label,
                            "confidence": round(avg_prob * 100, 1),
                            "code": code,
                            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                        }

                        self.state = self.STATE_OPERATING
                        self.thinking_progress = 100
                        logging.info(f"[DECISION LOCKED] Code [{code}] ({label}). Transmitting to Hardware Driver.")

                        if self.active_timer:
                            try:
                                self.active_timer.cancel()
                            except Exception:
                                pass

                        # Send command code to hardware driver
                        self.hardware.send_command(code)

                        # Database persistence
                        log_detection(category_upper, label, avg_prob, code)
                        log_system_event("INFO", "VISION", f"Autonomous Segregation: {label} ({code})")

                        # Safety fallback auto-reset after 12.0s cycle
                        self.active_timer = threading.Timer(12.0, self._auto_reset_operating_state)
                        self.active_timer.daemon = True
                        self.active_timer.start()

                    else:
                        self.state = self.STATE_WAITING
                        self.thinking_progress = 0

        self.broadcast_telemetry()

    def _auto_reset_operating_state(self):
        with self.lock:
            if self.state == self.STATE_OPERATING:
                logging.info("[STATE MACHINE] Safety timeout: Resetting arm operation back to WAITING.")
                self.state = self.STATE_WAITING
                self.thinking_progress = 0
                self.accumulated_scores.clear()
                self.sample_count = 0
                if hasattr(self.hardware, "current_angles"):
                    from backend.app.hardware.arduino_driver import SERVO_PRESETS
                    self.hardware.current_angles = SERVO_PRESETS.get("H", {}).copy()
        self.broadcast_telemetry()

    def handle_arm_done(self):
        with self.lock:
            if self.active_timer:
                try:
                    self.active_timer.cancel()
                except Exception:
                    pass
                self.active_timer = None

            logging.info("[STATE MACHINE] Arm completed movement cycle. Deterministically resetting to WAITING.")
            if self.state != self.STATE_EMERGENCY:
                self.state = self.STATE_WAITING
                self.thinking_progress = 0
                self.accumulated_scores.clear()
                self.sample_count = 0

        log_system_event("INFO", "HARDWARE", "Robotic Arm completed action and returned Home.")
        self.broadcast_telemetry()

    # --- Mode & Control Actions ---
    def set_mode(self, mode: str):
        mode_upper = mode.upper()
        if mode_upper in [self.MODE_AUTONOMOUS, self.MODE_MANUAL]:
            with self.lock:
                self.mode = mode_upper
                if mode_upper == self.MODE_MANUAL and self.state != self.STATE_EMERGENCY:
                    self.state = self.STATE_WAITING
                    self.thinking_progress = 0
            log_action("SET_MODE", payload=mode_upper)
            log_system_event("INFO", "CONTROL", f"Operating mode switched to {mode_upper}")
            self.broadcast_telemetry()
            return True, f"Mode switched to {mode_upper}"
        return False, f"Invalid mode '{mode}'"

    def trigger_manual_command(self, action: str, code: str = None):
        action_upper = action.upper()

        if action_upper == "STOP":
            return self.trigger_emergency_stop()
        elif action_upper in ["HOME", "RESET"]:
            return self.trigger_reset()

        if action_upper not in CATEGORY_TO_CODE:
            return False, f"Invalid manual category '{action}'"

        with self.lock:
            # Deterministic lockout: Prevent overlapping commands while sorting is in progress or in emergency stop
            if self.state in [self.STATE_OPERATING, self.STATE_EMERGENCY]:
                logging.warning(f"[CONTROL] Ignored '{action_upper}': System is in {self.state} state.")
                return False, f"Arm is currently in {self.state} state. Please wait or reset."

            code = CATEGORY_TO_CODE[action_upper]
            label = CATEGORY_LABELS[action_upper]

            self.state = self.STATE_OPERATING
            self.last_detection = {
                "id": f"det_{int(time.time()*1000)}",
                "category": action_upper,
                "label": label,
                "confidence": 100.0,
                "code": code,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }

            if self.active_timer:
                try:
                    self.active_timer.cancel()
                except Exception:
                    pass

            self.hardware.send_command(code)

            # Safety fallback auto-reset after 12.0s
            self.active_timer = threading.Timer(12.0, self._auto_reset_operating_state)
            self.active_timer.daemon = True
            self.active_timer.start()

        log_action("MANUAL_COMMAND", payload=f"{action_upper} ({code})")
        log_detection(action_upper, label, 1.0, code, status="MANUAL_OVERRIDE")
        self.broadcast_telemetry()
        return True, f"Manual command [{code}] ({label}) sent."

    def trigger_emergency_stop(self):
        with self.lock:
            if self.active_timer:
                try:
                    self.active_timer.cancel()
                except Exception:
                    pass
                self.active_timer = None
            self.state = self.STATE_EMERGENCY
            self.hardware.send_command("E")
        log_action("EMERGENCY_STOP")
        log_system_event("WARNING", "SAFETY", "EMERGENCY SAFETY STOP TRIGGERED!")
        self.broadcast_telemetry()
        return True, "Emergency Safety Stop triggered!"

    def trigger_reset(self):
        with self.lock:
            if self.active_timer:
                try:
                    self.active_timer.cancel()
                except Exception:
                    pass
                self.active_timer = None
            self.state = self.STATE_WAITING
            self.thinking_progress = 0
            self.hardware.send_command("H")
        log_action("RESET")
        log_system_event("INFO", "CONTROL", "System state reset to Home position.")
        self.broadcast_telemetry()
        return True, "System reset successfully."

    def set_thinking_duration(self, duration: float):
        with self.lock:
            self.thinking_duration = max(1.0, min(15.0, float(duration)))
        return self.thinking_duration

    def switch_serial_port(self, port: str, baud_rate: int = 19200):
        return self.connect_serial_port(port=port, baud_rate=baud_rate)

    def connect_serial_port(self, port: str, baud_rate: int = 19200):
        with self.lock:
            from backend.app.hardware.arduino_driver import ArduinoArmDriver
            if not isinstance(self.hardware, ArduinoArmDriver):
                if hasattr(self.hardware, "disconnect"):
                    self.hardware.disconnect()
                self.hardware = ArduinoArmDriver(port=port, baud_rate=baud_rate)
                self.hardware.register_done_callback(self.handle_arm_done)
                if hasattr(self.hardware, "register_log_callback"):
                    self.hardware.register_log_callback(self.broadcast_telemetry)
            self.hardware.connect(port=port, baud_rate=baud_rate)
        log_system_event("INFO", "HARDWARE", f"Arduino serial connection attempt on {port} @ {baud_rate} Baud")
        self.broadcast_telemetry()
        return self.hardware.get_hardware_status()

    def disconnect_serial_port(self):
        with self.lock:
            if hasattr(self.hardware, "disconnect"):
                self.hardware.disconnect()
        log_system_event("INFO", "HARDWARE", "Arduino serial port disconnected by user")
        self.broadcast_telemetry()
        return self.hardware.get_hardware_status() if hasattr(self.hardware, "get_hardware_status") else {"connected": False}

    def clear_serial_logs(self):
        if hasattr(self.hardware, "clear_serial_logs"):
            self.hardware.clear_serial_logs()
        self.broadcast_telemetry()
        return True

    # --- Telemetry Format (Matching Next.js types.ts) ---
    def get_telemetry_snapshot(self) -> Dict[str, Any]:
        with self.lock:
            arm_angles = self.hardware.get_servo_angles()
            stats_today = get_today_statistics()

            # Dynamic database counts (defaults to 0, no fake seeds)
            db_counts = stats_today.get("counts", {})
            counts = {
                "PLASTIC": db_counts.get("plastic", 0),
                "PAPER": db_counts.get("paper", 0),
                "METAL": db_counts.get("metal", 0),
                "GLASS": db_counts.get("glass", 0),
                "CARDBOARD": db_counts.get("cardboard", 0)
            }
            total_today = stats_today.get("total", 0)

            # Dynamic Real Hardware Status
            hw_status = self.hardware.get_hardware_status()
            hw_ok = hw_status.get("ok", False)
            hw_label = hw_status.get("label", "Arduino Disconnected")
            hw_detail = hw_status.get("detail", "No USB Serial device connected")
            serial_logs = hw_status.get("logs", [])
            avail_ports = hw_status.get("available_ports", [])

            # Dynamic Camera Status
            from backend.app.vision_service import vision_service
            is_real_cam = vision_service.is_physical_camera()
            cam_label = "USB Camera Feed Active" if is_real_cam else "Camera Video Feed (Virtual)"
            cam_detail = f"{settings.FRAME_WIDTH}×{settings.FRAME_HEIGHT} · {self.fps:.1f} FPS"

            # Dynamic AI Model Status
            model_info = vision_service.get_model_info()
            model_name = model_info.get("name", "YOLOv8n Prebuilt")
            ai_label = f"AI Engine: {model_name}"
            ai_detail = f"{model_info.get('engine', 'YOLO Object Detector')} · 5s Cycle"

            # Dynamic Servo Status (Active if Arduino is physically connected)
            if hw_ok:
                servo_label = "Servo Motors Calibrated & Ready"
                servo_detail = f"6-DOF PWM on Pins 4,5,6,10,11,12"
                servo_ok = True
            else:
                servo_label = "Servo Motors Offline (Standby)"
                servo_detail = "Awaiting Arduino Hardware Connection"
                servo_ok = False

            # Dynamic SQLite Status
            db_detail = f"waste_sorter.db · {total_today} items today"

            health = [
                {"key": "arduino", "label": hw_label, "detail": hw_detail, "ok": hw_ok},
                {"key": "camera", "label": cam_label, "detail": cam_detail, "ok": is_real_cam},
                {"key": "ai", "label": ai_label, "detail": ai_detail, "ok": model_info.get("ok", True)},
                {"key": "servo", "label": servo_label, "detail": servo_detail, "ok": servo_ok},
                {"key": "db", "label": "SQLite Database Connected", "detail": db_detail, "ok": True}
            ]

            # Calculate server uptime
            uptime_secs = int(time.time() - SERVER_START_TIME)
            hours, remainder = divmod(uptime_secs, 3600)
            minutes, seconds = divmod(remainder, 60)
            uptime_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

            return {
                "state": self.state,
                "mode": self.mode,
                "detectionActive": self.detection_active,
                "fps": round(self.fps, 1),
                "thinkingProgress": self.thinking_progress,
                "arm": arm_angles,
                "lastDetection": self.last_detection,
                "counts": counts,
                "hourlyThroughput": stats_today.get("hourly", []),
                "health": health,
                "connected": True,
                "hardwareConnected": hw_ok,
                "serialPort": hw_status.get("port", settings.SERIAL_PORT),
                "baudRate": hw_status.get("baud_rate", 19200),
                "availablePorts": avail_ports,
                "availablePortsInfo": hw_status.get("available_ports_info", []),
                "serialLogs": serial_logs,
                "uptime": uptime_str,
                "modelName": model_name,
                "wsActive": len(self.active_websockets) > 0
            }

state_manager = DashboardStateManager()
