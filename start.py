"""
Fashion Wardrobe Manager - Interactive Startup Launcher
Choose which frontend to start: Web, Desktop, or Mobile

Usage: python start.py
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def main():
    print("=" * 80)
    print("👗 FASHION WARDROBE MANAGER - STARTUP LAUNCHER")
    print("=" * 80)
    print("\nSelect which frontend to start:\n")
    print("   1️⃣  Web Frontend (Streamlit) - Browser-based")
    print("   2️⃣  Desktop Frontend (PyQt6) - Native GUI application")
    print("   3️⃣  Mobile Frontend (React Native) - Android/iOS")
    print("   0️⃣  Exit")
    print("\n" + "=" * 80)
    
    choice = input("\nEnter your choice (0-3): ").strip()
    
    if choice == "1":
        print("\n🌐 Starting Web Frontend...")
        subprocess.run([sys.executable, str(ROOT / "start_web.py")])
    
    elif choice == "2":
        print("\n🖥️  Starting Desktop Frontend...")
        subprocess.run([sys.executable, str(ROOT / "start_desktop.py")])
    
    elif choice == "3":
        print("\n📱 Starting Mobile Frontend...")
        subprocess.run([sys.executable, str(ROOT / "start_mobile.py")])
    
    elif choice == "0":
        print("\n👋 Goodbye!")
        sys.exit(0)
    
    else:
        print("\n❌ Invalid choice. Please enter 0-3")
        main()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Exiting...")
        sys.exit(0)
