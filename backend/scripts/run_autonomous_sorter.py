#!/usr/bin/env python3
"""
Autonomous Pick-and-Place Sorter CLI Entrypoint
Usage:
  python backend/scripts/run_autonomous_sorter.py --category plastic --cycles 5
"""

import argparse
import logging
from backend.robotics.control.autonomous_controller import AutonomousController

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def main():
    parser = argparse.ArgumentParser(description="Run Autonomous Vision-Guided Waste Segregation Cycle")
    parser.add_argument("--category", type=str, default="plastic", help="Target waste category (plastic, paper, cardboard, glass, metal)")
    parser.add_argument("--cycles", type=int, default=1, help="Number of pick-and-place cycles to execute")
    args = parser.parse_args()

    controller = AutonomousController()
    logging.info(f"Starting {args.cycles} Autonomous Pick-and-Place Cycles for category '{args.category}'...")

    for i in range(1, args.cycles + 1):
        logging.info(f"\n--- Cycle [{i}/{args.cycles}] ---")
        result = controller.run_autonomous_cycle(target_category=args.category)
        logging.info(f"Cycle Result: {result}")

if __name__ == "__main__":
    main()
