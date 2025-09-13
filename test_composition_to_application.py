"""
Test CompositionToApplicationProofStep functionality.
Tests converting (c∘b)da to cbda when both forms exist.
"""

import sys
sys.path.append('.')

from PyQt6.QtCore import QPointF
from PyQt6.QtWidgets import QApplication
from widget.object_node import Object
from widget.diagram_scene import DiagramScene
from core.proof_step import CompositionToApplicationProofStep

def test_composition_to_application():
    print("Testing CompositionToApplicationProofStep:")
    print("=" * 50)
    
    # Create QApplication instance
    app = QApplication.instance() or QApplication(sys.argv)
    
    # Create scene
    scene = DiagramScene()
    
    # Test Case 1: Node with both (c∘b)da and cbda elements
    print("\nTest Case 1: Node with both (c∘b)da and cbda")
    print("-" * 50)
    
    # Create a node with both composition and application forms
    node1 = Object(text="(c∘b)da, cbda:X")
    node1.setPos(QPointF(0, 0))
    scene.addItem(node1)
    
    print(f"Before: {node1.get_display_text()}")
    
    # Test if proof step is applicable
    is_applicable = CompositionToApplicationProofStep.is_applicable([node1], [])
    print(f"Is applicable: {is_applicable}")
    
    if is_applicable:
        # Apply the proof step
        proof_step = CompositionToApplicationProofStep(scene, [node1], [])
        proof_step.apply()
        
        print(f"After: {node1.get_display_text()}")
        print(f"Expected: '(c∘b)da=cbda:X'")
        print(f"Match: {node1.get_display_text() == '(c∘b)da=cbda:X'}")
        
        # Test undo
        proof_step.unapply()
        print(f"After undo: {node1.get_display_text()}")
    
    # Test Case 2: Node with complex composition
    print("\nTest Case 2: Node with complex composition (g∘h∘k)ab and ghkab")
    print("-" * 50)
    
    node2 = Object(text="(g∘h∘k)ab, ghkab, other:Y")
    node2.setPos(QPointF(100, 0))
    scene.addItem(node2)
    
    print(f"Before: {node2.get_display_text()}")
    
    is_applicable = CompositionToApplicationProofStep.is_applicable([node2], [])
    print(f"Is applicable: {is_applicable}")
    
    if is_applicable:
        proof_step = CompositionToApplicationProofStep(scene, [node2], [])
        proof_step.apply()
        
        print(f"After: {node2.get_display_text()}")
        expected = "(g∘h∘k)ab=ghkab, other:Y"
        print(f"Expected: '{expected}'")
        # Note: order might vary, so just check that both elements are converted to equality
        result_text = node2.get_display_text()
        has_equality = "=" in result_text and "(g∘h∘k)ab" in result_text and "ghkab" in result_text
        print(f"Contains expected equality: {has_equality}")
    
    # Test Case 3: Node with only composition (no matching application)
    print("\nTest Case 3: Node with only composition (no match)")
    print("-" * 50)
    
    node3 = Object(text="(f∘g)x, other:Z")
    node3.setPos(QPointF(200, 0))
    scene.addItem(node3)
    
    print(f"Before: {node3.get_display_text()}")
    
    is_applicable = CompositionToApplicationProofStep.is_applicable([node3], [])
    print(f"Is applicable: {is_applicable}")
    print("Should be False since no matching flattened form exists")
    
    # Test Case 4: Node with nested compositions
    print("\nTest Case 4: Node with nested composition ((a∘b)∘c)d and abcd")
    print("-" * 50)
    
    node4 = Object(text="((a∘b)∘c)d, abcd:W")
    node4.setPos(QPointF(300, 0))
    scene.addItem(node4)
    
    print(f"Before: {node4.get_display_text()}")
    
    is_applicable = CompositionToApplicationProofStep.is_applicable([node4], [])
    print(f"Is applicable: {is_applicable}")
    
    if is_applicable:
        proof_step = CompositionToApplicationProofStep(scene, [node4], [])
        proof_step.apply()
        
        print(f"After: {node4.get_display_text()}")
        # The flattening should remove all ∘ symbols
        has_equality = "=" in node4.get_display_text()
        print(f"Creates equality: {has_equality}")
    
    print("\n" + "=" * 50)
    print("Test completed!")

if __name__ == "__main__":
    test_composition_to_application()