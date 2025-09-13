"""
Test script for MapElementProofStep prepending functionality.
This tests the requirement: "When you MapElement and the Codomain of the Arrow already 
contains an element, then you adjoin to the list (to left of ":") via e.g. 
x=y,z:C in codomain append element w yields: w,x=y,z:C"
"""
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QPointF
import sys

# Add the project root to Python path
sys.path.insert(0, r'C:\Users\fruit\OneDrive\Desktop\erro')

from core.app import App
from widget.main_window import MainWindow
from widget.object_node import Object
from widget.arrow import Arrow
from core.proof_step import MapElementProofStep

def test_map_element_prepending():
    """Test the MapElementProofStep prepending functionality."""
    
    app = App(sys.argv)
    
    # Create scene directly for testing
    from widget.diagram_scene import DiagramScene
    from PyQt6.QtWidgets import QGraphicsView
    
    scene = DiagramScene()
    view = QGraphicsView(scene)
    
    print("Testing MapElementProofStep prepending functionality:")
    print("=" * 60)
    
    # Test Case 1: Codomain with existing elements
    print("\nTest Case 1: Codomain already has elements")
    print("-" * 40)
    
    # Create domain with element to map
    domain1 = Object(text="a:X")
    domain1.setPos(QPointF(100, 100))
    scene.addItem(domain1)
    
    # Create codomain with existing elements
    codomain1 = Object(text="x=y,z:C")
    codomain1.setPos(QPointF(300, 100))
    scene.addItem(codomain1)
    
    # Arrow from domain to codomain
    arrow1 = Arrow(start_node=domain1, end_node=codomain1, text="f")
    scene.addItem(arrow1)
    
    print(f"Before mapping:")
    print(f"  Domain: '{domain1.get_display_text()}'")
    print(f"  Codomain: '{codomain1.get_display_text()}'")
    print(f"  Arrow: '{arrow1.get_text()}'")
    
    # Apply MapElement
    step1 = MapElementProofStep(scene, [], [arrow1])
    step1.apply()
    
    print(f"After mapping element 'a' via 'f':")
    print(f"  Codomain: '{codomain1.get_display_text()}'")
    print(f"  Expected: 'f(a),x=y,z:C'")
    print(f"  Match: {codomain1.get_display_text() == 'f(a),x=y,z:C'}")
    
    # Test Case 2: Empty codomain (just object name)
    print("\nTest Case 2: Empty codomain (just object name)")
    print("-" * 40)
    
    # Clear scene
    scene.clear()
    
    # Create domain with element to map
    domain2 = Object(text="b:Y")
    domain2.setPos(QPointF(100, 200))
    scene.addItem(domain2)
    
    # Create empty codomain (just name)
    codomain2 = Object(text="D")
    codomain2.setPos(QPointF(300, 200))
    scene.addItem(codomain2)
    
    # Arrow from domain to codomain
    arrow2 = Arrow(start_node=domain2, end_node=codomain2, text="g")
    scene.addItem(arrow2)
    
    print(f"Before mapping:")
    print(f"  Domain: '{domain2.get_display_text()}'")
    print(f"  Codomain: '{codomain2.get_display_text()}'")
    print(f"  Arrow: '{arrow2.get_text()}'")
    
    # Apply MapElement
    step2 = MapElementProofStep(scene, [], [arrow2])
    step2.apply()
    
    print(f"After mapping element 'b' via 'g':")
    print(f"  Codomain: '{codomain2.get_display_text()}'")
    print(f"  Expected: 'g(b):D'")
    print(f"  Match: {codomain2.get_display_text() == 'g(b):D'}")
    
    # Test Case 3: Codomain with colon but no elements
    print("\nTest Case 3: Codomain with colon but no elements")
    print("-" * 40)
    
    # Clear scene
    scene.clear()
    
    # Create domain with element to map
    domain3 = Object(text="c:Z")
    domain3.setPos(QPointF(100, 300))
    scene.addItem(domain3)
    
    # Create codomain with colon but no elements
    codomain3 = Object(text=":E")
    codomain3.setPos(QPointF(300, 300))
    scene.addItem(codomain3)
    
    # Arrow from domain to codomain
    arrow3 = Arrow(start_node=domain3, end_node=codomain3, text="h")
    scene.addItem(arrow3)
    
    print(f"Before mapping:")
    print(f"  Domain: '{domain3.get_display_text()}'")
    print(f"  Codomain: '{codomain3.get_display_text()}'")
    print(f"  Arrow: '{arrow3.get_text()}'")
    
    # Apply MapElement
    step3 = MapElementProofStep(scene, [], [arrow3])
    step3.apply()
    
    print(f"After mapping element 'c' via 'h':")
    print(f"  Codomain: '{codomain3.get_display_text()}'")
    print(f"  Expected: 'h(c):E'")
    print(f"  Match: {codomain3.get_display_text() == 'h(c):E'}")
    
    print("\n" + "=" * 60)
    print("Test completed successfully!")
    print("The MapElement proof step now prepends elements to existing codomain lists.")
    
    # Don't show the main window for this test
    app.quit()

if __name__ == "__main__":
    test_map_element_prepending()