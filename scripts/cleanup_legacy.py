#!/usr/bin/env python3
"""
Clean up legacy duplicate root files after full-stack architecture migration.
"""
import os
import shutil

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FILES_TO_REMOVE = [
    "main.py",
    "model.py",
    "config.py",
    "iiot_communicator.py",
    "test_system.py",
    "robotic_hand.ino"
]

DIRS_TO_REMOVE = [
    "src",
    "phase1",
    "legacy_phase3",
    "3 phases architecture"
]

def cleanup():
    for fname in FILES_TO_REMOVE:
        fpath = os.path.join(ROOT_DIR, fname)
        if os.path.exists(fpath):
            try:
                os.remove(fpath)
                print(f"[REMOVED FILE] {fname}")
            except Exception as e:
                print(f"[ERROR] Could not remove {fname}: {e}")

    for dname in DIRS_TO_REMOVE:
        dpath = os.path.join(ROOT_DIR, dname)
        if os.path.exists(dpath):
            try:
                shutil.rmtree(dpath)
                print(f"[REMOVED DIR] {dname}")
            except Exception as e:
                print(f"[ERROR] Could not remove {dname}: {e}")

if __name__ == "__main__":
    cleanup()
