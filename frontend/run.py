#!/usr/bin/env python
"""
Frontend App Launcher
Starts the Streamlit app with proper configuration
"""

import sys
import os
from pathlib import Path
import subprocess

# Add frontend to path
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

# Set environment variables
os.environ.setdefault('BACKEND_URL', 'http://localhost:8000')
os.environ.setdefault('STREAMLIT_CLIENT_THEME_MODE', 'light')
os.environ.setdefault('STREAMLIT_CLIENT_TOOLBAR_MODE', 'developer')


def run_frontend():
    """Launch the Streamlit app"""
    print("🚀 Starting Fashion Wardrobe Frontend App...")
    print(f"   Backend URL: {os.environ.get('BACKEND_URL')}")
    print()
    
    try:
        subprocess.run([
            'streamlit', 'run',
            str(SCRIPT_DIR / 'app.py'),
            '--theme.primaryColor=#FF6B6B',
            '--theme.backgroundColor=#FFFFFF',
            '--theme.secondaryBackgroundColor=#F0F2F6',
            '--theme.textColor=#262730',
        ])
    except KeyboardInterrupt:
        print("\n✅ Shutting down...")


if __name__ == "__main__":
    run_frontend()
