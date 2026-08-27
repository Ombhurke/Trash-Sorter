#!/usr/bin/env python3
"""
Unified Production Full-Stack Launcher for Robotic Arm System
Launches the FastAPI Backend (Port 8000) and Next.js Frontend (Port 3000) concurrently.
Run with: python scripts/run_fullstack.py
"""
import sys
import os
import time
import subprocess
import signal

# Windows UTF-8 console output safe configuration
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(ROOT_DIR, "frontend")
sys.path.insert(0, ROOT_DIR)

def main():
    print("=================================================================")
    print("   [+] VEG QX - FULL-STACK ROBOTIC ARM SYSTEM (ALL SERVICES)")
    print("=================================================================")
    print("  * Backend API Base:   http://localhost:8000")
    print("  * WebSocket Feed:     ws://localhost:8000/ws")
    print("  * MJPEG Video Feed:   http://localhost:8000/api/video-feed")
    print("  * Frontend Web UI:    http://localhost:3000")
    print("=================================================================\n")

    processes = []

    try:
        # 1. Start Next.js Frontend Dev Server
        print("[1/2] Starting Next.js Web Dashboard (Port 3000)...")
        npm_cmd = "npm.cmd" if sys.platform.startswith("win") else "npm"
        frontend_proc = subprocess.Popen(
            [npm_cmd, "run", "dev"],
            cwd=FRONTEND_DIR,
            shell=sys.platform.startswith("win"),
        )
        processes.append(frontend_proc)

        # 2. Start FastAPI Backend Server
        print("[2/2] Starting FastAPI Backend Server (Port 8000)...")
        import uvicorn
        uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)

    except KeyboardInterrupt:
        print("\n[!] Shutting down full-stack services...")
    finally:
        for p in processes:
            try:
                if sys.platform.startswith("win"):
                    subprocess.call(["taskkill", "/F", "/T", "/PID", str(p.pid)])
                else:
                    p.terminate()
            except Exception:
                pass
        print("[OK] All full-stack services stopped cleanly.")

if __name__ == "__main__":
    main()
