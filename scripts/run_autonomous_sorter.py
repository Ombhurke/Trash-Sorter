#!/usr/bin/env python3
"""
Fully Autonomous Vision-Guided Waste Segregation Manipulator CLI Script.
Executes real-time Object 3D Pose Estimation -> ArUco Bin Detection -> Hand-Eye Coordinate Transformation -> Inverse Kinematics -> Motion Planning -> Low-level Serial Servo Stream.
Zero hardcoded servo angles or bin locations!
Usage:
    python scripts/run_autonomous_sorter.py --category plastic --cycles 3
"""

import sys
import os
import argparse
import time
import logging

# Ensure project root is in sys.path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from backend.robotics.control.autonomous_controller import AutonomousController

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def parse_args():
    parser = argparse.ArgumentParser(description="Autonomous Vision-Guided Robotic Manipulator")
    parser.add_argument(
        "--category",
        choices=["plastic", "paper", "cardboard", "glass", "metal"],
        default="plastic",
        help="Target waste category to process"
    )
    parser.add_argument(
        "--cycles",
        type=int,
        default=1,
        help="Number of autonomous pick-and-place cycles to execute"
    )
    return parser.parse_args()


def main():
    args = parse_args()

    logging.info("=================================================================")
    logging.info("  AUTONOMOUS VISION-GUIDED WASTE SEGREGATION ROBOTIC MANIPULATOR")
    logging.info("  Zero hardcoded angles | Real-time ArUco Bin Tracking | 6-DOF IK")
    logging.info("=================================================================")

    controller = AutonomousController()

    for cycle in range(1, args.cycles + 1):
        logging.info(f"\n--- EXECUTING AUTONOMOUS CYCLE [{cycle}/{args.cycles}] for '{args.category}' ---")
        result = controller.run_autonomous_cycle(target_category=args.category)
        logging.info(f"Cycle Result: {result}")
        if cycle < args.cycles:
            time.sleep(1.0)

    logging.info("\nAutonomous Sorter pipeline execution complete!")


if __name__ == "__main__":
    main()

