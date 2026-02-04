import os
import sys

# Add the project root to python path to make imports work easily
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.ui.app_window import AppWindow

def main():
    app = AppWindow()
    app.start()

if __name__ == "__main__":
    main()
