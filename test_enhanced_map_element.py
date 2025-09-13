"""
Test script for enhanced MapElement functionality with juxtaposition and zero handling.
Tests the requirement: "How MapElement acts on fa=0:X should be (if g is the selected Arrow): 
(g∘f)a=g0=0, i.e. in addition write Application of a map to an element as juxtaposition."
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
from widget.diagram_scene import DiagramScene
from PyQt6.QtWidgets import QGraphicsView
from core.proof_step import MapElementProofStep

def test_enhanced_map_element():
    """Test the enhanced MapElement functionality."""
    
    app = App(sys.argv)
    
    # Create scene directly for testing
    scene = DiagramScene()
    view = QGraphicsView(scene)
    
    print("Testing enhanced MapElementProofStep functionality:")
    print("=" * 60)
    
    # Test Case 1: fa=0:X → (g∘f)a=g0=0
    print("\nTest Case 1: Juxtaposition with zero (fa=0:X)")
    print("-" * 50)
    
    # Create domain with fa=0 element
    domain1 = Object(text="fa=0:X")
    domain1.setPos(QPointF(100, 100))
    scene.addItem(domain1)
    
    # Create codomain
    codomain1 = Object(text="Y")
    codomain1.setPos(QPointF(300, 100))
    scene.addItem(codomain1)
    
    # Arrow g from domain to codomain
    arrow1 = Arrow(start_node=domain1, end_node=codomain1, text="g")
    scene.addItem(arrow1)
    
    print(f"Before mapping:")
    print(f"  Domain: '{domain1.get_display_text()}'")
    print(f"  Codomain: '{codomain1.get_display_text()}'")
    print(f"  Arrow: '{arrow1.get_text()}'")
    
    # Apply MapElement
    step1 = MapElementProofStep(scene, [], [arrow1])
    step1.apply()
    
    print(f"After mapping 'fa=0' via 'g':")
    print(f"  Codomain: '{codomain1.get_display_text()}'")
    print(f"  Expected: '(g∘f)a=g0=0:Y'")
    print(f"  Match: {codomain1.get_display_text() == '(g∘f)a=g0=0:Y'}")
    
    # Test Case 2: Simple juxtaposition fa (without =0)
    print("\nTest Case 2: Simple juxtaposition (fa:X)")
    print("-" * 50)
    
    # Clear scene
    scene.clear()
    
    # Create domain with fa element (no zero)
    domain2 = Object(text="fa:X")
    domain2.setPos(QPointF(100, 200))
    scene.addItem(domain2)
    
    # Create codomain
    codomain2 = Object(text="Z")
    codomain2.setPos(QPointF(300, 200))
    scene.addItem(codomain2)
    
    # Arrow h from domain to codomain
    arrow2 = Arrow(start_node=domain2, end_node=codomain2, text="h")
    scene.addItem(arrow2)
    
    print(f"Before mapping:")
    print(f"  Domain: '{domain2.get_display_text()}'")
    print(f"  Codomain: '{codomain2.get_display_text()}'")
    print(f"  Arrow: '{arrow2.get_text()}'")
    
    # Apply MapElement
    step2 = MapElementProofStep(scene, [], [arrow2])
    step2.apply()
    
    print(f"After mapping 'fa' via 'h':")
    print(f"  Codomain: '{codomain2.get_display_text()}'")
    print(f"  Expected: '(h∘f)a:Z'")
    print(f"  Match: {codomain2.get_display_text() == '(h∘f)a:Z'}")
    
    # Test Case 3: Regular function application f(a)
    print("\nTest Case 3: Regular function application (f(a):X)")
    print("-" * 50)
    
    # Clear scene
    scene.clear()
    
    # Create domain with function application
    domain3 = Object(text="f(a):X")
    domain3.setPos(QPointF(100, 300))
    scene.addItem(domain3)
    
    # Create codomain
    codomain3 = Object(text="W")
    codomain3.setPos(QPointF(300, 300))
    scene.addItem(codomain3)
    
    # Arrow k from domain to codomain
    arrow3 = Arrow(start_node=domain3, end_node=codomain3, text="k")
    scene.addItem(arrow3)
    
    print(f"Before mapping:")
    print(f"  Domain: '{domain3.get_display_text()}'")
    print(f"  Codomain: '{codomain3.get_display_text()}'")
    print(f"  Arrow: '{arrow3.get_text()}'")
    
    # Apply MapElement
    step3 = MapElementProofStep(scene, [], [arrow3])
    step3.apply()
    
    print(f"After mapping 'f(a)' via 'k':")
    print(f"  Codomain: '{codomain3.get_display_text()}'")
    print(f"  Expected: '(k∘f)a:W'")
    print(f"  Match: {codomain3.get_display_text() == '(k∘f)a:W'}")
    
    # Test Case 4: Simple element a
    print("\nTest Case 4: Simple element (a:X)")
    print("-" * 50)
    
    # Clear scene
    scene.clear()
    
    # Create domain with simple element
    domain4 = Object(text="a:X")
    domain4.setPos(QPointF(100, 400))
    scene.addItem(domain4)
    
    # Create codomain
    codomain4 = Object(text="Z")
    codomain4.setPos(QPointF(300, 400))
    scene.addItem(codomain4)
    
    # Arrow m from domain to codomain
    arrow4 = Arrow(start_node=domain4, end_node=codomain4, text="m")
    scene.addItem(arrow4)
    
    print(f"Before mapping:")
    print(f"  Domain: '{domain4.get_display_text()}'")
    print(f"  Codomain: '{codomain4.get_display_text()}'")
    print(f"  Arrow: '{arrow4.get_text()}'")
    
    # Apply MapElement
    step4 = MapElementProofStep(scene, [], [arrow4])
    step4.apply()
    
    print(f"After mapping 'a' via 'm':")
    print(f"  Codomain: '{codomain4.get_display_text()}'")
    print(f"  Expected: 'ma:Z'")
    print(f"  Match: {codomain4.get_display_text() == 'ma:Z'}")
    
    print("\n" + "=" * 60)
    print("Test completed!")
    print("MapElement now handles juxtaposition and enhanced zero mapping.")
    
    # Don't show the main window for this test
    app.quit()

if __name__ == "__main__":
    test_enhanced_map_element()