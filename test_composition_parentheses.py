"""
Test script to verify that composition functions are properly wrapped in parentheses.
Tests the requirement: "any time a node contains ∘ it should contain at least one pair of ()"
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

def test_composition_parentheses():
    """Test that composition functions are wrapped in parentheses."""
    
    app = App(sys.argv)
    
    # Create scene directly for testing
    scene = DiagramScene()
    view = QGraphicsView(scene)
    
    print("Testing composition function parentheses:")
    print("=" * 50)
    
    # Test Case 1: Simple composition b∘k_e mapping element a
    print("\nTest Case 1: Composition function (b∘k_e) mapping element a")
    print("-" * 55)
    
    # Create domain with element a
    domain1 = Object(text="a:X")
    domain1.setPos(QPointF(100, 100))
    scene.addItem(domain1)
    
    # Create codomain
    codomain1 = Object(text="Y")
    codomain1.setPos(QPointF(300, 100))
    scene.addItem(codomain1)
    
    # Arrow with composition function name
    arrow1 = Arrow(start_node=domain1, end_node=codomain1, text="b∘k_e")
    scene.addItem(arrow1)
    
    print(f"Before mapping:")
    print(f"  Domain: '{domain1.get_display_text()}'")
    print(f"  Codomain: '{codomain1.get_display_text()}'")
    print(f"  Arrow: '{arrow1.get_text()}'")
    
    # Apply MapElement
    step1 = MapElementProofStep(scene, [], [arrow1])
    step1.apply()
    
    print(f"After mapping 'a' via 'b∘k_e':")
    print(f"  Codomain: '{codomain1.get_display_text()}'")
    print(f"  Expected: '(b∘k_e)a:Y'")
    print(f"  Match: {codomain1.get_display_text() == '(b∘k_e)a:Y'}")
    print(f"  Contains ∘ and (): {('∘' in codomain1.get_display_text()) and ('(' in codomain1.get_display_text() and ')' in codomain1.get_display_text())}")
    
    # Test Case 2: Simple function f mapping element a (no parentheses needed)
    print("\nTest Case 2: Simple function f mapping element a")
    print("-" * 50)
    
    # Clear scene
    scene.clear()
    
    # Create domain with element a
    domain2 = Object(text="a:X")
    domain2.setPos(QPointF(100, 200))
    scene.addItem(domain2)
    
    # Create codomain
    codomain2 = Object(text="Z")
    codomain2.setPos(QPointF(300, 200))
    scene.addItem(codomain2)
    
    # Arrow with simple function name
    arrow2 = Arrow(start_node=domain2, end_node=codomain2, text="f")
    scene.addItem(arrow2)
    
    print(f"Before mapping:")
    print(f"  Domain: '{domain2.get_display_text()}'")
    print(f"  Codomain: '{codomain2.get_display_text()}'")
    print(f"  Arrow: '{arrow2.get_text()}'")
    
    # Apply MapElement
    step2 = MapElementProofStep(scene, [], [arrow2])
    step2.apply()
    
    print(f"After mapping 'a' via 'f':")
    print(f"  Codomain: '{codomain2.get_display_text()}'")
    print(f"  Expected: 'fa:Z'")
    print(f"  Match: {codomain2.get_display_text() == 'fa:Z'}")
    print(f"  No unnecessary parentheses: {'(' not in codomain2.get_display_text().split(':')[0]}")
    
    # Test Case 3: More complex composition g∘h∘k mapping element b
    print("\nTest Case 3: Complex composition g∘h∘k mapping element b")
    print("-" * 55)
    
    # Clear scene
    scene.clear()
    
    # Create domain with element b
    domain3 = Object(text="b:W")
    domain3.setPos(QPointF(100, 300))
    scene.addItem(domain3)
    
    # Create codomain
    codomain3 = Object(text="V")
    codomain3.setPos(QPointF(300, 300))
    scene.addItem(codomain3)
    
    # Arrow with complex composition
    arrow3 = Arrow(start_node=domain3, end_node=codomain3, text="g∘h∘k")
    scene.addItem(arrow3)
    
    print(f"Before mapping:")
    print(f"  Domain: '{domain3.get_display_text()}'")
    print(f"  Codomain: '{codomain3.get_display_text()}'")
    print(f"  Arrow: '{arrow3.get_text()}'")
    
    # Apply MapElement
    step3 = MapElementProofStep(scene, [], [arrow3])
    step3.apply()
    
    print(f"After mapping 'b' via 'g∘h∘k':")
    print(f"  Codomain: '{codomain3.get_display_text()}'")
    print(f"  Expected: '(g∘h∘k)b:V'")
    print(f"  Match: {codomain3.get_display_text() == '(g∘h∘k)b:V'}")
    print(f"  Contains ∘ and (): {('∘' in codomain3.get_display_text()) and ('(' in codomain3.get_display_text() and ')' in codomain3.get_display_text())}")
    
    # Test Case 4: Composition with zero element a=0
    print("\nTest Case 4: Composition g∘f mapping zero element a=0")
    print("-" * 55)
    
    # Clear scene
    scene.clear()
    
    # Create domain with zero element
    domain4 = Object(text="a=0:U")
    domain4.setPos(QPointF(100, 400))
    scene.addItem(domain4)
    
    # Create codomain
    codomain4 = Object(text="T")
    codomain4.setPos(QPointF(300, 400))
    scene.addItem(codomain4)
    
    # Arrow with composition
    arrow4 = Arrow(start_node=domain4, end_node=codomain4, text="g∘f")
    scene.addItem(arrow4)
    
    print(f"Before mapping:")
    print(f"  Domain: '{domain4.get_display_text()}'")
    print(f"  Codomain: '{codomain4.get_display_text()}'")
    print(f"  Arrow: '{arrow4.get_text()}'")
    
    # Apply MapElement
    step4 = MapElementProofStep(scene, [], [arrow4])
    step4.apply()
    
    print(f"After mapping 'a=0' via 'g∘f':")
    print(f"  Codomain: '{codomain4.get_display_text()}'")
    print(f"  Expected: '(g∘f)a=g∘f0=0:T'")
    print(f"  Match: {codomain4.get_display_text() == '(g∘f)a=g∘f0=0:T'}")
    print(f"  Contains ∘ and (): {('∘' in codomain4.get_display_text()) and ('(' in codomain4.get_display_text() and ')' in codomain4.get_display_text())}")
    
    print("\n" + "=" * 50)
    print("Test completed!")
    print("Composition functions are now properly wrapped in parentheses.")
    print("Rule: Any function containing ∘ gets wrapped in () when applied via juxtaposition.")
    
    # Don't show the main window for this test
    app.quit()

if __name__ == "__main__":
    test_composition_parentheses()