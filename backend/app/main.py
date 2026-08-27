import time
import json
from typing import Optional, Dict, Any
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.database import init_db, get_db, Detection, SystemLog, UserAction, get_today_statistics
from backend.app.state_manager import state_manager, CODE_TO_CATEGORY, CATEGORY_TO_CODE
from backend.app.vision_service import vision_service

app = FastAPI(
    title="Veg QX — Robotic Arm Sorter IoT API",
    description="Full-Stack Backend API & Real-time WebSockets for Vision-Guided Waste Segregation System",
    version="2.0.0"
)

# Enable CORS for Next.js frontend (http://localhost:3000) and dev clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:8000", "http://127.0.0.1:8000", "*"],
    allow_origin_regex=r"http://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ManualControlRequest(BaseModel):
    action: Optional[str] = None
    category: Optional[str] = None
    code: Optional[str] = None

class ModeRequest(BaseModel):
    mode: str

@app.on_event("startup")
async def startup_event():
    import asyncio
    state_manager.set_event_loop(asyncio.get_running_loop())
    init_db()
    vision_service.start()

@app.on_event("shutdown")
def shutdown_event():
    vision_service.stop()

@app.get("/")
def read_root():
    return {
        "status": "online",
        "system": "Veg QX — Robotic Arm Sorter Backend",
        "docs": "/docs",
        "websocket": "/ws",
        "video_feed": "/api/video-feed"
    }

# --- Telemetry & Health Endpoints ---
@app.get("/api/telemetry")
def get_telemetry():
    return state_manager.get_telemetry_snapshot()

@app.get("/api/status")
def get_status():
    snapshot = state_manager.get_telemetry_snapshot()
    snapshot["servo_angles"] = snapshot.get("arm", {})
    return snapshot

@app.get("/api/health")
def get_health():
    snapshot = state_manager.get_telemetry_snapshot()
    return snapshot.get("health", [])

@app.get("/api/statistics")
def get_statistics():
    snapshot = state_manager.get_telemetry_snapshot()
    return {
        "counts": snapshot.get("counts", {}),
        "total": sum(snapshot.get("counts", {}).values())
    }

@app.get("/api/statistics/today")
def get_statistics_today():
    return get_statistics()

# --- Database History Endpoints ---
@app.get("/api/detections")
def get_detections(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Detection)
    if category:
        query = query.filter(Detection.category == category.upper())
    total = query.count()
    items = query.order_by(Detection.timestamp.desc()).offset(offset).limit(limit).all()
    
    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "items": [
            {
                "id": f"det_{item.id}",
                "timestamp": item.timestamp.isoformat(),
                "category": item.category,
                "label": item.display_name,
                "confidence": round(item.confidence * 100 if item.confidence <= 1.0 else item.confidence, 1),
                "code": item.letter_code,
                "status": item.status
            }
            for item in items
        ]
    }

@app.get("/api/logs")
def get_logs(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    logs = db.query(SystemLog).order_by(SystemLog.timestamp.desc()).limit(limit).all()
    return [
        {
            "id": l.id,
            "timestamp": l.timestamp.isoformat(),
            "level": l.level,
            "source": l.source,
            "message": l.message
        }
        for l in logs
    ]

# --- Arm Movement & Control Endpoints ---
@app.post("/api/control/manual")
def manual_control(req: ManualControlRequest):
    act = req.action or req.category or "PLASTIC"
    success, message = state_manager.trigger_manual_command(act, req.code)
    if not success:
        raise HTTPException(status_code=400, detail=message)
    return {"ok": True, "status": "success", "message": message}

@app.post("/api/control/mode")
def set_mode_control(req: ModeRequest):
    success, message = state_manager.set_mode(req.mode)
    if not success:
        raise HTTPException(status_code=400, detail=message)
    return {"ok": True, "message": message}

@app.post("/api/control/emergency-stop")
def emergency_stop_control():
    success, message = state_manager.trigger_emergency_stop()
    return {"ok": True, "message": message}

@app.post("/api/control/reset")
def reset_control():
    success, message = state_manager.trigger_reset()
    return {"ok": True, "message": message}

@app.post("/api/control/home")
def home_control():
    return reset_control()

# --- Camera & Vision Detection Control Endpoints ---
@app.post("/api/vision/toggle")
def toggle_vision_detection():
    if vision_service.camera_active:
        return stop_vision_detection()
    else:
        return start_vision_detection()

@app.post("/api/vision/start")
def start_vision_detection():
    vision_service.open_camera()
    active = state_manager.set_detection_active(True)
    return {"ok": True, "detectionActive": True, "cameraActive": True, "message": "Camera hardware and AI detection started"}

@app.post("/api/vision/stop")
def stop_vision_detection():
    vision_service.release_camera()
    active = state_manager.set_detection_active(False)
    return {"ok": True, "detectionActive": False, "cameraActive": False, "message": "Camera hardware turned OFF and AI detection paused"}

# --- Settings & Dynamic Serial COM Port Endpoints ---
class SettingsUpdateRequest(BaseModel):
    serial_port: Optional[str] = None
    baud_rate: Optional[int] = None
    confidence_threshold: Optional[float] = None
    thinking_duration: Optional[float] = None
    roi_size: Optional[float] = None
    camera_device: Optional[int] = None
    auto_start: Optional[bool] = None
    log_detections: Optional[bool] = None
    return_to_home: Optional[bool] = None

# --- Dedicated Serial Hardware & COM Port Endpoints ---
class SerialConnectRequest(BaseModel):
    port: str
    baud_rate: Optional[int] = 19200

class SerialSendRequest(BaseModel):
    command: str
    label: Optional[str] = None

@app.get("/api/serial/ports")
def get_serial_ports():
    try:
        import serial.tools.list_ports
        ports = serial.tools.list_ports.comports()
        hw_status = state_manager.hardware.get_hardware_status() if state_manager.hardware else {}
        connected_port = hw_status.get("port") if hw_status.get("connected") else None
        
        return {
            "ports": [
                {
                    "port": p.device,
                    "description": p.description or p.device,
                    "hwid": p.hwid or ""
                }
                for p in ports
            ],
            "connected_port": connected_port,
            "connected": hw_status.get("connected", False),
            "baud_rate": hw_status.get("baud_rate", 19200)
        }
    except Exception as e:
        return {"ports": [], "connected": False, "error": str(e)}

@app.post("/api/serial/connect")
def connect_serial(req: SerialConnectRequest):
    status = state_manager.connect_serial_port(req.port, req.baud_rate or 19200)
    return {
        "ok": status.get("ok", False),
        "connected": status.get("connected", False),
        "port": status.get("port", req.port),
        "baud_rate": status.get("baud_rate", req.baud_rate),
        "message": status.get("detail", "Connection processed")
    }

@app.post("/api/serial/disconnect")
def disconnect_serial():
    status = state_manager.disconnect_serial_port()
    return {
        "ok": True,
        "connected": False,
        "message": "Serial port disconnected"
    }

@app.get("/api/serial/status")
def get_serial_status():
    if hasattr(state_manager, "hardware") and state_manager.hardware:
        return state_manager.hardware.get_hardware_status()
    return {"connected": False, "ok": False, "label": "No Hardware Driver", "logs": []}

@app.post("/api/serial/send")
def send_raw_serial(req: SerialSendRequest):
    cmd = req.command.strip()
    if not cmd:
        raise HTTPException(status_code=400, detail="Command cannot be empty")
    
    # Check if this matches a waste category or home
    act = CODE_TO_CATEGORY.get(cmd.upper(), cmd.upper())
    if act in CATEGORY_TO_CODE or act in ["HOME", "RESET", "STOP"]:
        success, message = state_manager.trigger_manual_command(act, cmd.upper())
    else:
        success = state_manager.hardware.send_command(cmd)
        message = f"Transmitted '{cmd}' over serial"
    
    return {"ok": success, "message": message}

@app.post("/api/serial/clear-logs")
def clear_serial_logs():
    state_manager.clear_serial_logs()
    return {"ok": True, "message": "Serial logs cleared"}

@app.get("/api/settings")
def get_settings():
    try:
        import serial.tools.list_ports
        ports = [p.device for p in serial.tools.list_ports.comports()]
    except Exception:
        ports = []
    
    hw_status = state_manager.hardware.get_hardware_status() if state_manager.hardware else {}
    current_port = hw_status.get("port", "COM3")
    
    if current_port and current_port not in ports and current_port != "MOCK":
        ports.insert(0, current_port)
    if not ports:
        ports = ["COM1", "COM2", "COM3", "COM4", "COM5"]

    conf_thresh = getattr(vision_service.classifier, "confidence_threshold", 0.40) if vision_service.classifier else 0.40
    thinking_dur = getattr(state_manager, "thinking_duration", 5.0)
    roi_ratio = getattr(vision_service, "roi_ratio", 0.50)

    return {
        "available_ports": ports,
        "serial_port": current_port,
        "baud_rate": hw_status.get("baud_rate", 19200),
        "confidence_threshold": round(conf_thresh * 100),
        "thinking_duration": round(thinking_dur, 1),
        "roi_size": round(roi_ratio * 100),
        "camera_device": getattr(vision_service, "camera_index", 0),
        "resolution": "1280 × 720",
        "api_base": "http://localhost:8000",
        "auto_start": True,
        "log_detections": True,
        "return_to_home": True
    }

@app.post("/api/settings")
def update_settings(req: SettingsUpdateRequest):
    if req.serial_port:
        baud = req.baud_rate or 19200
        state_manager.switch_serial_port(req.serial_port, baud)

    if req.confidence_threshold is not None:
        val = req.confidence_threshold / 100.0 if req.confidence_threshold > 1.0 else req.confidence_threshold
        vision_service.set_confidence_threshold(val)

    if req.thinking_duration is not None:
        state_manager.set_thinking_duration(req.thinking_duration)

    if req.roi_size is not None:
        val = req.roi_size / 100.0 if req.roi_size > 1.0 else req.roi_size
        vision_service.set_roi_ratio(val)

    return get_settings()

# --- Video Feed Stream (Motion JPEG) ---
def gen_video_frames():
    while True:
        frame_bytes = vision_service.get_latest_jpeg()
        if frame_bytes:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        time.sleep(0.015)  # ~64 FPS streaming interval

@app.get("/api/video-feed")
def video_feed():
    return StreamingResponse(
        gen_video_frames(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

# --- WebSocket Endpoint ---
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await state_manager.connect_ws(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data) if isinstance(data, str) else {}
                action = msg.get("action")
                if action:
                    state_manager.trigger_manual_command(action, msg.get("code"))
            except Exception:
                pass
    except WebSocketDisconnect:
        state_manager.disconnect_ws(websocket)
