import unittest
from backend.robotics.kinematics.forward_kinematics import ForwardKinematics
from backend.robotics.kinematics.inverse_kinematics import InverseKinematics
from backend.phase1.perception.bin_detector import BinDetector
from backend.phase1.calibration.hand_eye_calibrator import HandEyeCalibrator
from backend.hardware.factory import get_hardware_driver

class TestBackendSystem(unittest.TestCase):
    def test_kinematics_solvers(self):
        fk = ForwardKinematics()
        ik = InverseKinematics()
        angles, ok = ik.solve_ik((150.0, 100.0, 150.0))
        self.assertEqual(len(angles), 6)
        x, y, z = fk.compute_fk(angles)
        self.assertIsInstance(x, float)

    def test_perception_and_calibration(self):
        detector = BinDetector()
        calibrator = HandEyeCalibrator()
        poses = detector.detect_bins(None)
        self.assertIn("PLASTIC", poses)
        cam_xyz = (poses["PLASTIC"].x_cam, poses["PLASTIC"].y_cam, poses["PLASTIC"].z_cam)
        robot_xyz = calibrator.camera_to_robot_frame(cam_xyz)
        self.assertEqual(len(robot_xyz), 3)

    def test_hardware_driver_factory(self):
        driver = get_hardware_driver(mode="mock")
        self.assertTrue(driver.is_connected())
        self.assertTrue(driver.send_command("H"))

if __name__ == "__main__":
    unittest.main()
