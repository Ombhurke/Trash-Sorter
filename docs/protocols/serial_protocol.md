# Serial Communication Protocol & Pinout Specification

## 🔌 Serial Port Configuration
* **Baud Rate:** `19200 Baud` (Matches `Serial.begin(19200)` in `firmware/robotic_hand.ino`)
* **Data Bits:** 8 | **Parity:** None | **Stop Bits:** 1

---

## ✉️ Transmitted Commands (Host PC -> Arduino)

### Single-Byte Category Commands
When an object is classified, the host PC transmits a single ASCII character:

| Code | Waste Category | Target Bin | Servo Function Call |
| :---: | :--- | :--- | :--- |
| **`P`** | Plastic Waste | Right Bin (Blue) | `throwPlastic()` |
| **`A`** | Paper Waste | Far Right Bin (Green) | `throwPaper()` |
| **`C`** | Cardboard Waste | Back Bin (Brown) | `throwCardboard()` |
| **`G`** | Glass Waste | Left Bin (Gray) | `throwGlass()` |
| **`M`** | Metal Waste | Far Left Bin (Yellow) | `throwMetal()` |

### Streamed Joint Angle Commands (Continuous Joint Vector Stream)
In continuous joint control mode, the host streams joint angles in CSV format:
```
S,<BaseAngle>,<ShoulderAngle>,<ElbowAngle>,<Wrist1Angle>,<Wrist2Angle>,<HandAngle>\n
```
* Example: `S,90,45,130,90,110,15`

---

## 📩 Received Responses (Arduino -> Host PC)

| Signal String | Description |
| :--- | :--- |
| `"Robotic Arm Ready"` | Emitted upon startup completion in `setup()`. |
| `"Done"` | Emitted after executing a throw sequence and returning to `homeState()`. Signals state machine to unlock vision inference. |

---

## ⚡ Arduino Servo Pin Mapping

| Servo Joint | Arduino Digital Pin | Servo Model | Function |
| :--- | :---: | :--- | :--- |
| **Base** | Pin 4 | MG996R | Horizontal rotation left/right |
| **Shoulder** | Pin 11 | MG996R | Primary vertical arm extension |
| **Elbow** | Pin 12 | MG996R | Secondary reach extension |
| **Wrist Pitch** | Pin 10 | MG995 | Gripper elevation tilt |
| **Wrist Roll** | Pin 6 | MG995 | Object orientation alignment |
| **Gripper / Hand** | Pin 5 | MG995 | Claw open/close action |
