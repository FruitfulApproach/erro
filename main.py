"""
Main application entry point for Pythom DAG Diagram Editor.
"""
import sys
from PyQt6.QtCore import Qt

from core.app import PythomApp
from main_window import MainWindow


def main():
    """Main application function."""
    # Create the application
    app = PythomApp(sys.argv)
    
    # Enable high DPI scaling
    # Note: High DPI scaling is enabled by default in PyQt6
    
    # Create and show the main window
    window = MainWindow()
    window.show()
    
    # Run the application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
