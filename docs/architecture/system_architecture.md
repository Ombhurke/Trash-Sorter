# Autonomous Vision-Guided Robotic Manipulator Architecture

```
Camera (USB Video Feed)
   │
   ▼
Object Detection & Pose Estimator
(OpenCV + OpenAI CLIP / TFLite -> X_c, Y_c, Z_c)
   │
   ▼
Dynamic Bin Detector
(ArUco Markers / AprilTags IDs 0..4 -> X_b, Y_b, Z_b)
   │
   ▼
Hand-Eye Coordinate Calibration Matrix
(T_cam_to_robot: Camera Frame -> Robot Base Frame)
   │
   ▼
Dynamic 6-DOF Inverse Kinematics (IK Solver)
(Solves theta1..theta6 dynamically for target X,Y,Z)
   │
   ▼
Joint-Space Motion Planner & State Machine
(S-curve Quintic Trajectory / Category Sequences)
   │
   ▼
Low-Level Arduino PWM Servo Driver
(Listens for single-letter codes 'P','A','C','G','M','H' over Serial at 19200 Baud)
   │
   ▼
Destination Bin Deposit Verification
(6-DOF Arm deposits waste into target dustbin & returns Home)
```

---

## 🔑 Key Autonomous Modules

### 1. Hand-Eye Calibration Matrix (`backend/phase1/calibration/hand_eye_calibrator.py`)
Computes 3D point transformation:
$$\begin{bmatrix} X_r \\ Y_r \\ Z_r \\ 1 \end{bmatrix} = \mathbf{T}_{\text{cam}}^{\text{robot}} \begin{bmatrix} X_c \\ Y_c \\ Z_c \\ 1 \end{bmatrix}$$

### 2. Dynamic Bin Detector (`backend/phase1/perception/bin_detector.py`)
Scans camera frames for ArUco markers attached to waste bins:
* **Tag ID 0:** Plastic Bin
* **Tag ID 1:** Paper Bin
* **Tag ID 2:** Cardboard Bin
* **Tag ID 3:** Glass Bin
* **Tag ID 4:** Metal Bin

### 3. Analytical 6-DOF Inverse Kinematics (`backend/robotics/kinematics/inverse_kinematics.py`)
Analytically calculates joint angles $(\theta_1, \theta_2, \theta_3, \theta_4, \theta_5, \theta_6)$ given arbitrary 3D target Cartesian coordinates $(X, Y, Z)$ and end-effector pitch angle $\phi$. Zero hardcoded servo angles!

### 4. Motion Planner (`backend/robotics/planning/motion_planner.py`)
Generates quintic S-curve joint space trajectories:
1. `APPROACH`: Move arm above detected object
2. `PICK`: Lower arm & close gripper
3. `LIFT`: Elevate object to safe clearance altitude
4. `TRANSPORT`: Rotate base & move arm to dynamic bin coordinates
5. `RELEASE`: Open gripper to deposit waste into target bin

### 5. Low-Level Arduino Driver (`firmware/robotic_hand.ino`)
Pure low-level PWM servo executor receiving commands over USB serial at 19,200 Baud.
