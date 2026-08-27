#!/usr/bin/env python3
"""
Fully Autonomous Vision-Guided Waste Segregation Manipulator CLI Script.
Executes real-time Object 3D Pose Estimation -> ArUco Bin Detection -> Hand-Eye Coordinate Transformation -> Inverse Kinematics -> Motion Planning -> Low-level Serial Servo Stream.
Zero hardcoded servo angles or bin locations!
"""

import sys
import os
import argparse
import time

# Add src to PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from waste_segregation.config import SystemConfig, WasteCategory
from waste_segregation.core import AutonomousController
from waste_segregation.utils import setup_logger


def parse_args():
    parser = argparse.ArgumentParser(description="Autonomous Vision-Guided Robotic Manipulator")
    parser.add_argument("--category", choices=["plastic", "paper", "cardboard", "glass", "metal"], default="plastic", help="Target waste category to process")
    parser.add_argument("--cycles", type=int, default=3, help="Number of autonomous pick-and-place cycles to execute")
    return parser.parse_args()


def main():
    args = parse_args()

    config = SystemConfig()
    logger = setup_logger("Autonomous_Sorter", log_dir=config.logs_dir)

    logger.info("=================================================================")
    logger.info("  AUTONOMOUS VISION-GUIDED WASTE SEGREGATION ROBOTIC MANIPULATOR")
    logger.info("  Zero hardcoded angles | Real-time ArUco Bin Tracking | 6-DOF IK")
    logger.info("=================================================================")

    controller = AutonomousController(system_config=config)

    cat_map = {
        "plastic": WasteCategory.PLASTIC,
        "paper": WasteCategory.PAPER,
        "cardboard": WasteCategory.CARDBOARD,
        "glass": WasteCategory.GLASS,
        "metal": WasteCategory.METAL
    }
    target_cat = cat_map[args.category]

    for cycle in range(1, args.cycles + 1):
        logger.info(f"\n--- EXECUTING AUTONOMOUS CYCLE [{cycle}/{args.cycles}] ---")
        result = controller.run_autonomous_cycle(target_cat)
        logger.info(f"Cycle Result: {result}")
        time.sleep(1.0)

    logger.info("\nAutonomous Sorter pipeline execution complete!")


if __name__ == "__main__":
    main()
