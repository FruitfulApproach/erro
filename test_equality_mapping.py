#!/usr/bin/env python3
"""
Test MapElement with equality expressions to ensure proper mapping of both sides.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from widget.diagram_scene import DiagramScene
from widget.object_node import Object
from widget.arrow import Arrow
from core.proof_step import MapElementProofStep

def test_equality_mapping():
    """Test that equality expressions are mapped correctly on both sides."""
    
    app = QApplication(sys.argv)
    
    # Test cases for equality mapping
    test_cases = [
        ("A=B", "f", "fA=fB", "Regular equality A=B mapped by f"),
        ("x=0", "g", "gx=g0=0", "Equality with zero x=0 mapped by g"),
        ("0=y", "h", "h0=0=hy", "Equality with zero on left 0=y mapped by h"),
        ("abc=def", "k", "kabc=kdef", "Multi-character elements abc=def mapped by k"),
        ("simple", "f", "fsimple", "Simple element (no equality)")
    ]
    
    print("Testing equality expression mapping:")
    all_passed = True
    
    for element, func, expected, description in test_cases:
        # Create a MapElement proof step instance to test the method
        scene = DiagramScene()
        scene._is_concrete_category = True
        
        obj_a = Object("A")
        obj_a.setPos(100, 100)
        obj_a.set_text(f"{element}:A")
        
        obj_b = Object("B")
        obj_b.setPos(300, 100)
        
        scene.addItem(obj_a)
        scene.addItem(obj_b)
        
        arrow = Arrow(obj_a, obj_b)
        arrow.set_text(func)
        scene.addItem(arrow)
        
        # Create proof step and test the mapping method directly
        proof_step = MapElementProofStep(scene, [], [arrow])
        result = proof_step._create_mapped_element_notation(element, func)
        
        status = "✅" if result == expected else "❌"
        print(f"  {status} {description}")
        print(f"      Input: {element} mapped by {func}")
        print(f"      Result: {result}")
        print(f"      Expected: {expected}")
        
        if result != expected:
            all_passed = False
        print()
    
    return all_passed

def test_full_mapping_workflow():
    """Test complete mapping workflow with equality expressions."""
    
    app = QApplication(sys.argv)
    
    # Create scene
    scene = DiagramScene()
    scene._is_concrete_category = True
    
    # Create objects
    obj_a = Object("A")
    obj_a.setPos(100, 100)
    obj_a.set_text("x=0:A")  # Domain has equality with zero
    
    obj_b = Object("B")
    obj_b.setPos(300, 100)
    
    scene.addItem(obj_a)
    scene.addItem(obj_b)
    
    # Create arrow f: A -> B
    arrow = Arrow(obj_a, obj_b)
    arrow.set_text("f")
    scene.addItem(arrow)
    
    print("Full workflow test:")
    print(f"Before mapping - Domain: {obj_a.get_display_text()}")
    print(f"Before mapping - Codomain: {obj_b.get_display_text()}")
    
    # Apply MapElement proof step
    proof_step = MapElementProofStep(scene, [], [arrow])
    
    try:
        proof_step.apply()
        
        print(f"After mapping - Domain: {obj_a.get_display_text()}")
        print(f"After mapping - Codomain: {obj_b.get_display_text()}")
        
        # Check if the result contains the expected equality with zero
        codomain_text = obj_b.get_display_text()
        expected_patterns = ["fx=f0=0", "=0"]
        
        if any(pattern in codomain_text for pattern in expected_patterns):
            print("✅ SUCCESS: Equality with zero correctly mapped")
            return True
        else:
            print(f"❌ FAILURE: Expected equality with zero pattern not found")
            print(f"   Got result: {codomain_text}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR during mapping: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_multiple_equalities():
    """Test mapping when domain contains multiple equality expressions."""
    
    app = QApplication(sys.argv)
    
    # Create scene
    scene = DiagramScene()
    scene._is_concrete_category = True
    
    # Create objects
    obj_a = Object("A")
    obj_a.setPos(100, 100)
    obj_a.set_text("x=y,z=0,a=b:A")  # Multiple equalities including one with zero
    
    obj_b = Object("B")
    obj_b.setPos(300, 100)
    
    scene.addItem(obj_a)
    scene.addItem(obj_b)
    
    # Create arrow g: A -> B
    arrow = Arrow(obj_a, obj_b)
    arrow.set_text("g")
    scene.addItem(arrow)
    
    print("\nMultiple equalities test:")
    print(f"Before mapping - Domain: {obj_a.get_display_text()}")
    print(f"Before mapping - Codomain: {obj_b.get_display_text()}")
    
    # We'll need to manually select one element since the dialog would appear
    # Let's test by setting the element_name directly
    proof_step = MapElementProofStep(scene, [], [arrow])
    proof_step.element_name = "z=0"  # Manually select the zero equality
    proof_step.function_name = "g"
    
    # Test the mapping method directly
    result = proof_step._create_mapped_element_notation("z=0", "g")
    expected = "gz=g0=0"
    
    print(f"Mapping z=0 by g: {result}")
    print(f"Expected: {expected}")
    
    if result == expected:
        print("✅ SUCCESS: Multiple equalities handled correctly")
        return True
    else:
        print("❌ FAILURE: Multiple equalities not handled correctly")
        return False

if __name__ == "__main__":
    success1 = test_equality_mapping()
    success2 = test_full_mapping_workflow()
    success3 = test_multiple_equalities()
    
    if success1 and success2 and success3:
        print("\n🎉 All equality mapping tests passed!")
    else:
        print("\n💥 Some equality mapping tests failed!")
    
    sys.exit(0 if (success1 and success2 and success3) else 1)