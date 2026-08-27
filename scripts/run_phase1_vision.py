#!/usr/bin/env python3
"""
Phase 1: Real-Time Vision Waste Sorter CLI Entry Point.
Executes OpenCV Video Stream + YOLO / Heuristic Classification + Arduino PySerial Protocol.
Usage:
    python scripts/run_phase1_vision.py
"""

import sys
import os

# Ensure project root is in sys.path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from backend.phase1.main import main

if __name__ == "__main__":
    main()

