#!/usr/bin/env python3
"""
Quick debugging script to test mouse events on nodes.
"""
import sys
from core.app import App
from widget.main_window import MainWindow

def debug_node_mouse_events():
    """Add debug prints to node mouse events."""
    from widget.node import Node
    
    original_mouse_press = Node.mousePressEvent
    original_mouse_release = Node.mouseReleaseEvent
    
    def debug_mouse_press(self, event):
        print(f"Node {self} mousePressEvent: {event.pos()}")
        return original_mouse_press(self, event)
    
    def debug_mouse_release(self, event):
        print(f"Node {self} mouseReleaseEvent: {event.pos()}")
        return original_mouse_release(self, event)
    
    Node.mousePressEvent = debug_mouse_press
    Node.mouseReleaseEvent = debug_mouse_release

if __name__ == "__main__":
    # Create the App instance instead of QApplication
    app = App(sys.argv)
    
    # Add debugging
    debug_node_mouse_events()
    
    # Create main window
    window = MainWindow()
    window.show()
    
    # Start event loop
    sys.exit(app.exec())
