#!/usr/bin/env python3
"""
Ensures clean project structure for frontend directory.
"""
import os
import shutil

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V0_DIR = os.path.join(ROOT_DIR, "v0")
FRONTEND_DIR = os.path.join(ROOT_DIR, "frontend")

def sync():
    if os.path.exists(FRONTEND_DIR):
        print(f"[OK] Production frontend directory '{FRONTEND_DIR}' is active.")
        return

    if os.path.exists(V0_DIR):
        shutil.copytree(V0_DIR, FRONTEND_DIR, ignore=shutil.ignore_patterns(".next", "node_modules", "pnpm-lock.yaml"))
        print(f"Synced {V0_DIR} -> {FRONTEND_DIR}")

if __name__ == "__main__":
    sync()
