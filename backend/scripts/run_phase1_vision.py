#!/usr/bin/env python3
"""
Phase 1 Vision Waste Classifier Sorter Launcher
Usage:
  python backend/scripts/run_phase1_vision.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.phase1.main import main

if __name__ == "__main__":
    main()

