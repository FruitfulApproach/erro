"""
Main application entry point for Pythom DAG Diagram Editor.
"""
import sys
from PyQt6.QtCore import Qt

from core.app import App
from widget.main_window import MainWindow


def main():
    """Main application function."""
    # Create the application
    app = App(sys.argv)
    
    # Enable high DPI scaling
    # Note: High DPI scaling is enabled by default in PyQt6
    
    # Create and show the main window
    window = MainWindow()
    
    # Restore previous session if available
    try:
        window.restore_session_data()
    except Exception as e:
        print(f"Could not restore previous session: {e}")
        # If restoration fails, create a default diagram
        if window.tab_widget.count() == 0:
            window.create_new_diagram()
    
    window.show()
    
    # Run the application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
