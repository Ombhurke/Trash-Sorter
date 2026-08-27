#!/usr/bin/env python3
"""
Phase 1: Real-Time Vision Waste Sorter CLI Entry Point.
Executes OpenCV Video Stream + OpenAI CLIP Zero-Shot Classification + Arduino PySerial Protocol.
"""

import sys
import os

# Add src to PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from waste_segregation.config import SystemConfig
from waste_segregation.vision import OptimizedWasteClassifier, HUDRenderer
from waste_segregation.hardware import ArduinoBridge, CameraBridge
from waste_segregation.core import ThreadSafeStateMachine
from waste_segregation.utils import setup_logger

import cv2
import time
import queue
import threading


def main():
    config = SystemConfig()
    logger = setup_logger("Phase1_Vision", log_dir=config.logs_dir)

    logger.info("Initializing Phase 1 Hardware Interfaces...")
    arduino = ArduinoBridge(
        port=config.hardware.SERIAL_PORT,
        baud_rate=config.hardware.BAUD_RATE,
        mock=config.hardware.MOCK_HARDWARE
    )

    state_machine = ThreadSafeStateMachine(arduino)
    arduino.on_done_callback = state_machine.handle_arduino_done

    logger.info("Initializing CLIP Vision Model...")
    classifier = OptimizedWasteClassifier(confidence_threshold=config.hardware.CONFIDENCE_THRESHOLD)
    renderer = HUDRenderer()
    camera = CameraBridge(camera_index=config.hardware.CAMERA_INDEX)

    if not camera.start():
        logger.error("Could not open camera stream.")
        return

    print("\n=======================================================")
    print("  PHASE 1: REAL-TIME WASTE SEGREGATION VISION SYSTEM")
    print("=======================================================")
    print("Controls:")
    print("  [R] - Reload / Reset State Lock")
    print("  [Q] / [ESC] - Quit Application")
    print("=======================================================\n")

    prev_time = time.time()

    try:
        while True:
            frame = camera.read_frame()
            if frame is None:
                break

            curr_time = time.time()
            fps = 1.0 / (curr_time - prev_time + 1e-6)
            prev_time = curr_time

            roi_crop = camera.get_roi_crop(frame)

            # Analyze frame if model is not locked
            snapshot = state_machine.get_snapshot()
            if snapshot["state"] != ThreadSafeStateMachine.STATE_ARM_OPERATING:
                analysis = classifier.analyze_frame(roi_crop)
                state_machine.update_analysis(analysis)

            display_frame = renderer.render(frame, snapshot, arduino.mock, fps)
            cv2.imshow("Phase 1 Waste Sorter Live Feed", display_frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == 27:
                break
            elif key == ord('r') or key == ord('R'):
                state_machine.reload_reset()

    finally:
        camera.release()
        cv2.destroyAllWindows()
        arduino.close()
        logger.info("Phase 1 Sorter shutdown cleanly.")


if __name__ == "__main__":
    main()
