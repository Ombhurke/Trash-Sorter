import time
import unittest
from backend.app.state_manager import DashboardStateManager, CATEGORY_TO_CODE, CODE_TO_CATEGORY

class TestSortingLifecycle(unittest.TestCase):
    def setUp(self):
        self.sm = DashboardStateManager()
        self.sm.trigger_reset()

    def test_state_initial_waiting(self):
        snap = self.sm.get_telemetry_snapshot()
        self.assertEqual(snap["state"], "WAITING")
        self.assertEqual(snap["wsActive"], False)
        self.assertIn("health", snap)
        self.assertIn("counts", snap)

    def test_single_command_lifecycle_plastic(self):
        # Trigger Plastic [P]
        success, msg = self.sm.trigger_manual_command("PLASTIC", "P")
        self.assertTrue(success)
        
        # Immediate state should be OPERATING
        snap = self.sm.get_telemetry_snapshot()
        self.assertEqual(snap["state"], "OPERATING")
        self.assertEqual(snap["lastDetection"]["category"], "PLASTIC")
        self.assertEqual(snap["lastDetection"]["code"], "P")

        # Concurrent/Duplicate trigger while OPERATING must be REJECTED
        dup_success, dup_msg = self.sm.trigger_manual_command("PLASTIC", "P")
        self.assertFalse(dup_success)
        self.assertIn("Arm is currently in OPERATING state", dup_msg)

        # Wait for simulated completion cycle (2.5s simulated delay)
        time.sleep(3.0)

        # State should be back to WAITING
        snap_after = self.sm.get_telemetry_snapshot()
        self.assertEqual(snap_after["state"], "WAITING")

    def test_all_categories_lifecycle(self):
        categories = [
            ("PLASTIC", "P"),
            ("PAPER", "A"),
            ("METAL", "M"),
            ("GLASS", "G"),
            ("CARDBOARD", "C"),
        ]

        for cat, code in categories:
            with self.subTest(category=cat, code=code):
                # Ensure in WAITING
                self.assertEqual(self.sm.state, "WAITING")
                
                success, msg = self.sm.trigger_manual_command(cat, code)
                self.assertTrue(success, f"Failed for {cat} [{code}]: {msg}")
                self.assertEqual(self.sm.state, "OPERATING")
                self.assertEqual(self.sm.last_detection["category"], cat)
                self.assertEqual(self.sm.last_detection["code"], code)

                # Wait for completion
                time.sleep(3.0)
                self.assertEqual(self.sm.state, "WAITING", f"Failed to reset to WAITING for {cat}")

    def test_emergency_stop_and_reset(self):
        # Trigger sorting
        self.sm.trigger_manual_command("METAL", "M")
        self.assertEqual(self.sm.state, "OPERATING")

        # Emergency stop overrides operating
        success, msg = self.sm.trigger_emergency_stop()
        self.assertTrue(success)
        self.assertEqual(self.sm.state, "EMERGENCY")

        # In EMERGENCY, sorting should be blocked
        success, msg = self.sm.trigger_manual_command("PLASTIC", "P")
        self.assertFalse(success)

        # Reset recovers to WAITING
        success, msg = self.sm.trigger_reset()
        self.assertTrue(success)
        self.assertEqual(self.sm.state, "WAITING")

    def test_serial_connect_disconnect_resilience(self):
        # Attempt connection to non-existent port (e.g. COM99)
        status = self.sm.connect_serial_port("COM99", 19200)
        self.assertFalse(status.get("connected", True))
        
        # Telemetry snapshot should still work and backend must remain fully functional
        snap = self.sm.get_telemetry_snapshot()
        self.assertFalse(snap["hardwareConnected"])

        # Sorting should still execute safely in offline/simulated mode
        success, msg = self.sm.trigger_manual_command("GLASS", "G")
        self.assertTrue(success)
        time.sleep(3.0)
        self.assertEqual(self.sm.state, "WAITING")

if __name__ == "__main__":
    unittest.main()
