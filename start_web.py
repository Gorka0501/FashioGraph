"""
Start Web Frontend (Streamlit) with Backend
Usage: python start_web.py
"""

import subprocess
import time
import sys
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VENV_PYTHON = ROOT / ".venv" / "Scripts" / "python.exe"
FRONTEND_DIR = ROOT / "frontend"

print("=" * 80)
print("👗 FASHION WARDROBE - WEB FRONTEND (STREAMLIT)")
print("=" * 80)

# Verify paths
print("\n🔍 Checking setup...")
print(f"   Project root: {ROOT}")
print(f"   Python exe: {VENV_PYTHON}")
print(f"   Frontend dir: {FRONTEND_DIR}")

if not VENV_PYTHON.exists():
    print(f"\n❌ ERROR: Python executable not found at {VENV_PYTHON}")
    print("   Please run: python -m venv .venv")
    sys.exit(1)

if not FRONTEND_DIR.exists():
    print(f"\n❌ ERROR: Frontend directory not found at {FRONTEND_DIR}")
    sys.exit(1)

print("   ✅ All paths verified")

# Start backend
print("\n📦 Starting Backend (FastAPI)...")
print("   Port: 8000")
print("   Docs: http://localhost:8000/docs")
print("   Health: http://localhost:8000/health")

try:
    backend = subprocess.Popen(
        [str(VENV_PYTHON), "-m", "uvicorn", "app.main:app", "--host", "localhost", "--port", "8000", "--reload", "--use-colors"],
        cwd=str(ROOT),
        bufsize=1,  # Line buffered
        universal_newlines=True
    )
    print(f"   ✅ Backend started (PID: {backend.pid})")
except Exception as e:
    print(f"   ❌ Failed to start backend: {e}")
    sys.exit(1)

# Wait for backend to start
print("\n⏳ Waiting for backend to initialize (10 seconds)...")
time.sleep(10)

# Check if backend is still running
if backend.poll() is not None:
    print(f"   ❌ Backend failed to start!")
    sys.exit(1)

# Start web frontend
print("\n🎨 Starting Web Frontend (Streamlit)...")
print("   Port: 8501")
print("   URL: http://localhost:8501")

try:
    frontend = subprocess.Popen(
        [str(VENV_PYTHON), "-m", "streamlit", "run", "app.py", "--client.showErrorDetails=true"],
        cwd=str(FRONTEND_DIR)
    )
    print(f"   ✅ Frontend started (PID: {frontend.pid})")
except Exception as e:
    print(f"   ❌ Failed to start frontend: {e}")
    backend.terminate()
    sys.exit(1)

print("\n" + "=" * 80)
print("✅ WEB FRONTEND IS RUNNING!")
print("=" * 80)
print("\n📍 Access URLs:")
print("   🎨 Web Frontend: http://localhost:8501")
print("   📦 Backend:      http://localhost:8000")
print("   📚 API Docs:     http://localhost:8000/docs")
print("\n⚠️  Press Ctrl+C to stop all services")
print("=" * 80 + "\n")

try:
    # Wait for frontend to complete (blocking)
    frontend.wait()
except KeyboardInterrupt:
    print("\n\n🛑 Stopping services...")
    frontend.terminate()
    backend.terminate()
    try:
        frontend.wait(timeout=3)
    except subprocess.TimeoutExpired:
        frontend.kill()
    try:
        backend.wait(timeout=3)
    except subprocess.TimeoutExpired:
        backend.kill()
    print("✅ Done")
