#!/usr/bin/env python3
"""
Phase 2 IoT Dashboard FastAPI Backend Server Launcher
Usage:
  python backend/scripts/run_phase2_backend.py
"""

import sys
import os
import uvicorn

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

if __name__ == "__main__":
    print("=================================================================")
    print("   VEG QX — IOT DASHBOARD FASTAPI BACKEND SERVER (PHASE 2)")
    print("=================================================================")
    print("  REST API Base URL:  http://localhost:8000")
    print("  Interactive Docs:   http://localhost:8000/docs")
    print("  WebSocket Feed:     ws://localhost:8000/ws")
    print("  MJPEG Video Feed:   http://localhost:8000/api/video-feed")
    print("=================================================================\n")
    
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
