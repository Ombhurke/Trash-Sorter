# IIoT 6-DOF Robotic Arm Trash Sorter (Phase 1 & Phase 2)

An industrial AI vision and full-stack IoT platform for automated waste segregation using a 6-DOF robotic manipulator and prebuilt YOLOv8 / CLIP computer vision.

---

## 🏗️ Canonical Project Structure

```text
Trash-Sorter/
├── docs/
│   ├── architecture/
│   │   └── system_architecture.md
│   └── protocols/
│       └── serial_protocol.md
├── firmware/
│   ├── robotic_arm_smooth_shoulder.ino
│   └── robotic_hand.ino
├── backend/
│   ├── app/
│   │   ├── hardware/
│   │   │   ├── arduino_driver.py
│   │   │   ├── base_driver.py
│   │   │   ├── factory.py
│   │   │   └── mock_driver.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── main.py
│   │   ├── state_manager.py
│   │   └── vision_service.py
│   ├── ml/
│   │   └── inference/
│   │       └── classifier.py
│   ├── phase1/
│   │   ├── calibration/
│   │   ├── perception/
│   │   ├── config.py
│   │   └── main.py
│   ├── robotics/
│   │   ├── control/
│   │   ├── kinematics/
│   │   └── planning/
│   ├── pyproject.toml
│   ├── requirements.txt
│   └── waste_sorter.db
├── frontend/
│   ├── app/
│   ├── components/
│   ├── lib/
│   ├── services/
│   └── package.json
├── scripts/
│   ├── cleanup_legacy.py
│   ├── run_autonomous_sorter.py
│   ├── run_fullstack.py
│   ├── run_phase1_vision.py
│   ├── run_phase2_backend.py
│   └── sync_frontend.py
├── README.md
└── requirements.txt
```

---

## ⚡ Serial Command Matrix (`robotic_hand.ino` @ 19200 Baud)

| Waste Category | Transmitted Code | Arduino Firmware Action | Target Predefined Dustbin |
| :--- | :---: | :--- | :--- |
| **Plastic Waste** | **`P`** | `pickUpObject()` $\rightarrow$ `throwPlastic()` | 🟦 **Right Bin (Blue)** |
| **Paper Waste** | **`A`** | `pickUpObject()` $\rightarrow$ `throwPaper()` | 🟩 **Far Right Bin (Green)** |
| **Cardboard Waste** | **`C`** | `pickUpObject()` $\rightarrow$ `throwCardboard()` | 🟫 **Back Bin (Brown)** |
| **Glass Waste** | **`G`** | `pickUpObject()` $\rightarrow$ `throwGlass()` | ⬜ **Left Bin (Gray)** |
| **Metal Waste** | **`M`** | `pickUpObject()` $\rightarrow$ `throwMetal()` | 🟨 **Far Left Bin (Yellow)** |
| **Home Position** | **`H`** | `homeState()` (Returns servos to 90°) | 🏠 **Calibration Home** |

---

## 🚀 How to Run

### 1. Run Complete Full-Stack Platform (Frontend + Backend)
```powershell
python scripts/run_fullstack.py
```
* **Frontend Web Dashboard:** [http://localhost:3000](http://localhost:3000)
* **Backend API & Swagger Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
* **Live MJPEG Video Stream:** [http://localhost:8000/api/video-feed](http://localhost:8000/api/video-feed)

### 2. Run Autonomous Sorter Engine Standalone
```powershell
python scripts/run_autonomous_sorter.py
```

### 3. Run Phase 1 Vision Perception Test
```powershell
python scripts/run_phase1_vision.py
```

### 4. Run Phase 2 Backend Only
```powershell
python scripts/run_phase2_backend.py
```