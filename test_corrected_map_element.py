"""
Test script for corrected MapElementProofStep functionality.
"""
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QPointF
import sys

# Add the project root to Python path
sys.path.insert(0, r'C:\Users\fruit\OneDrive\Desktop\erro')

from core.app import PythomApplication
from widget.main_window import MainWindow
from widget.object_node import Object
from widget.arrow import Arrow
from core.proof_step import MapElementProofStep

def test_corrected_map_element():
    """Test the corrected MapElementProofStep functionality."""
    
    app = PythomApplication(sys.argv)
    main_window = MainWindow()
    
    # Get the current scene
    scene = main_window.get_current_diagram_scene()
    scene.is_concrete_category = True  # Enable concrete category features
    
    # Create test objects
    # Domain with elements
    domain = Object(text="a, b, c : X")
    domain.setPos(QPointF(100, 100))
    scene.addItem(domain)
    
    # Codomain 
    codomain = Object(text="B")
    codomain.setPos(QPointF(300, 100))
    scene.addItem(codomain)
    
    # Arrow (function) from domain to codomain
    arrow = Arrow(start_node=domain, end_node=codomain, text="f")
    scene.addItem(arrow)
    
    # Test applicability
    objects = []
    arrows = [arrow]
    
    print("Testing corrected MapElementProofStep:")
    print(f"Domain display text: '{domain.get_display_text()}'")
    print(f"Domain base name: '{domain.get_text()}'")
    print(f"Codomain display text: '{codomain.get_display_text()}'")
    print(f"Codomain base name: '{codomain.get_text()}'")
    print(f"Is applicable: {MapElementProofStep.is_applicable(objects, arrows)}")
    print(f"Button text: {MapElementProofStep.button_text(objects, arrows)}")
    
    print("\nTest completed successfully!")
    
    # Don't show the main window for this test
    app.quit()

if __name__ == "__main__":
    test_corrected_map_element()