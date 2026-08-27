import time
import json
import unittest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.state_manager import state_manager

class TestEndToEndApiAndWebSocket(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        state_manager.trigger_reset()

    def test_health_and_telemetry_endpoints(self):
        res = self.client.get("/api/telemetry")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["state"], "WAITING")
        self.assertIn("counts", data)
        self.assertIn("health", data)

        res_health = self.client.get("/api/health")
        self.assertEqual(res_health.status_code, 200)
        self.assertIsInstance(res_health.json(), list)

    def test_manual_sorting_command_and_lockout(self):
        # 1. Trigger Plastic [P]
        res = self.client.post("/api/control/manual", json={"category": "PLASTIC", "code": "P"})
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json()["ok"])

        # 2. Immediate telemetry check - must be OPERATING
        snap = self.client.get("/api/telemetry").json()
        self.assertEqual(snap["state"], "OPERATING")
        self.assertEqual(snap["lastDetection"]["category"], "PLASTIC")

        # 3. Duplicate trigger while OPERATING must return 400 Bad Request
        dup_res = self.client.post("/api/control/manual", json={"category": "PLASTIC", "code": "P"})
        self.assertEqual(dup_res.status_code, 400)
        self.assertIn("Arm is currently in OPERATING state", dup_res.json()["detail"])

        # 4. Wait for completion routine (2.5s)
        time.sleep(3.0)

        # 5. After completion, state MUST be WAITING and backend MUST be online
        snap_after = self.client.get("/api/telemetry").json()
        self.assertEqual(snap_after["state"], "WAITING")

        # 6. Another item (e.g. Metal [M]) can now be sorted normally
        res_metal = self.client.post("/api/control/manual", json={"category": "METAL", "code": "M"})
        self.assertEqual(res_metal.status_code, 200)
        self.assertEqual(self.client.get("/api/telemetry").json()["state"], "OPERATING")

        time.sleep(3.0)
        self.assertEqual(self.client.get("/api/telemetry").json()["state"], "WAITING")

    def test_websocket_telemetry_stream(self):
        with self.client.websocket_connect("/ws") as ws:
            # Receive initial snapshot
            initial_msg = ws.receive_text()
            data = json.loads(initial_msg)
            self.assertEqual(data["state"], "WAITING")

            # Send manual throw command via REST
            res = self.client.post("/api/control/manual", json={"category": "PAPER", "code": "A"})
            self.assertEqual(res.status_code, 200)

            # Receive OPERATING update over WebSocket
            operating_msg = ws.receive_text()
            op_data = json.loads(operating_msg)
            self.assertEqual(op_data["state"], "OPERATING")
            self.assertEqual(op_data["lastDetection"]["category"], "PAPER")

            # Wait for completion callback -> WebSocket receives WAITING update
            final_state = None
            for _ in range(5):
                msg = ws.receive_text()
                data = json.loads(msg)
                if data["state"] == "WAITING":
                    final_state = "WAITING"
                    break
            self.assertEqual(final_state, "WAITING")

if __name__ == "__main__":
    unittest.main()
