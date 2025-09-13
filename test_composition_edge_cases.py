"""
Additional test cases for CompositionToApplicationProofStep.
Tests edge cases and complex scenarios.
"""

import sys
sys.path.append('.')

from PyQt6.QtCore import QPointF
from PyQt6.QtWidgets import QApplication
from widget.object_node import Object
from widget.diagram_scene import DiagramScene
from core.proof_step import CompositionToApplicationProofStep

def test_edge_cases():
    print("Testing CompositionToApplicationProofStep Edge Cases:")
    print("=" * 60)
    
    # Create QApplication instance
    app = QApplication.instance() or QApplication(sys.argv)
    
    # Create scene
    scene = DiagramScene()
    
    # Test Case 1: Multiple pairs in same node
    print("\nTest Case 1: Multiple composition-application pairs")
    print("-" * 60)
    
    node1 = Object(text="(a∘b)x, abx, (c∘d)y, cdy:X")
    node1.setPos(QPointF(0, 0))
    scene.addItem(node1)
    
    print(f"Before: {node1.get_display_text()}")
    
    is_applicable = CompositionToApplicationProofStep.is_applicable([node1], [])
    print(f"Is applicable: {is_applicable}")
    
    if is_applicable:
        proof_step = CompositionToApplicationProofStep(scene, [node1], [])
        proof_step.apply()
        
        result = node1.get_display_text()
        print(f"After: {result}")
        
        # Both pairs should be converted to equalities
        has_first = "(a∘b)x=abx" in result
        has_second = "(c∘d)y=cdy" in result
        print(f"Has first equality: {has_first}")
        print(f"Has second equality: {has_second}")
        print(f"Both converted: {has_first and has_second}")
    
    # Test Case 2: Mixed with existing equalities
    print("\nTest Case 2: Mixed with existing equalities")
    print("-" * 60)
    
    node2 = Object(text="(f∘g)a, fga, x=y, other:Y")
    node2.setPos(QPointF(100, 0))
    scene.addItem(node2)
    
    print(f"Before: {node2.get_display_text()}")
    
    is_applicable = CompositionToApplicationProofStep.is_applicable([node2], [])
    print(f"Is applicable: {is_applicable}")
    
    if is_applicable:
        proof_step = CompositionToApplicationProofStep(scene, [node2], [])
        proof_step.apply()
        
        result = node2.get_display_text()
        print(f"After: {result}")
        
        # Should preserve existing equality and add new one
        has_new_eq = "(f∘g)a=fga" in result
        has_old_eq = "x=y" in result
        has_other = "other" in result
        print(f"Has new equality: {has_new_eq}")
        print(f"Preserves old equality: {has_old_eq}")
        print(f"Preserves other element: {has_other}")
    
    # Test Case 3: Triple nested composition
    print("\nTest Case 3: Triple nested composition")
    print("-" * 60)
    
    node3 = Object(text="(((p∘q)∘r)∘s)z, pqrsz:Z")
    node3.setPos(QPointF(200, 0))
    scene.addItem(node3)
    
    print(f"Before: {node3.get_display_text()}")
    
    is_applicable = CompositionToApplicationProofStep.is_applicable([node3], [])
    print(f"Is applicable: {is_applicable}")
    
    if is_applicable:
        proof_step = CompositionToApplicationProofStep(scene, [node3], [])
        proof_step.apply()
        
        result = node3.get_display_text()
        print(f"After: {result}")
        
        # Should flatten all nested parentheses and compositions
        expected = "(((p∘q)∘r)∘s)z=pqrsz:Z"
        print(f"Expected: {expected}")
        print(f"Match: {result == expected}")
    
    # Test Case 4: Complex compositions with subscripts/superscripts
    print("\nTest Case 4: Complex function names")
    print("-" * 60)
    
    node4 = Object(text="(f₁∘g₂)a, f₁g₂a:W")
    node4.setPos(QPointF(300, 0))
    scene.addItem(node4)
    
    print(f"Before: {node4.get_display_text()}")
    
    is_applicable = CompositionToApplicationProofStep.is_applicable([node4], [])
    print(f"Is applicable: {is_applicable}")
    
    if is_applicable:
        proof_step = CompositionToApplicationProofStep(scene, [node4], [])
        proof_step.apply()
        
        result = node4.get_display_text()
        print(f"After: {result}")
        print(f"Should handle unicode characters correctly")
    
    # Test Case 5: No applicable case - only one form exists
    print("\nTest Case 5: Not applicable - only composition form")
    print("-" * 60)
    
    node5 = Object(text="(h∘k)b, other_element:V")
    node5.setPos(QPointF(400, 0))
    scene.addItem(node5)
    
    print(f"Before: {node5.get_display_text()}")
    
    is_applicable = CompositionToApplicationProofStep.is_applicable([node5], [])
    print(f"Is applicable: {is_applicable}")
    print("Should be False - no matching flattened form")
    
    print("\n" + "=" * 60)
    print("Edge case testing completed!")

if __name__ == "__main__":
    test_edge_cases()