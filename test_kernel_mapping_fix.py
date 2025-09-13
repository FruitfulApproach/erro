#!/usr/bin/env python3
"""
Test MapElement with kernel function notation to ensure proper composition.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from widget.diagram_scene import DiagramScene
from widget.object_node import Object
from widget.arrow import Arrow
from core.proof_step import MapElementProofStep

def test_kernel_map_element():
    """Test that 𝐤(e)a mapped by e becomes (e∘𝐤(e))a, not (e∘k)e."""
    
    app = QApplication(sys.argv)
    
    # Create scene
    scene = DiagramScene()
    
    # Create objects
    obj_b = Object("B")
    obj_b.setPos(100, 100)
    # Set domain to have kernel element 𝐤(e)a
    obj_b.set_text("𝐤(e)a:B")
    
    obj_c = Object("C") 
    obj_c.setPos(300, 100)
    
    scene.addItem(obj_b)
    scene.addItem(obj_c)
    
    # Create arrow e: B -> C
    arrow = Arrow(obj_b, obj_c)
    arrow.set_text("e")
    scene.addItem(arrow)
    
    print("Test: Mapping kernel element 𝐤(e)a by function e")
    print(f"Before mapping - Domain: {obj_b.get_display_text()}")
    print(f"Before mapping - Codomain: {obj_c.get_display_text()}")
    
    # Apply MapElement proof step
    proof_step = MapElementProofStep(scene, [], [arrow])
    
    try:
        proof_step.apply()
        
        print(f"After mapping - Domain: {obj_b.get_display_text()}")
        print(f"After mapping - Codomain: {obj_c.get_display_text()}")
        
        # Check if the result is correct
        codomain_text = obj_c.get_display_text()
        expected_pattern = "(e∘𝐤(e))a"
        
        if expected_pattern in codomain_text:
            print(f"✅ SUCCESS: Found correct pattern '{expected_pattern}' in result")
            print(f"   Full result: {codomain_text}")
            return True
        else:
            print(f"❌ FAILURE: Expected pattern '{expected_pattern}' not found")
            print(f"   Got result: {codomain_text}")
            
            # Check for the incorrect pattern that was happening before
            if "(e∘k)e" in codomain_text or "e∘k" in codomain_text:
                print("   ⚠️  Found incorrect composition pattern!")
            return False
            
    except Exception as e:
        print(f"❌ ERROR during mapping: {e}")
        return False

def test_simple_element_mapping():
    """Test that simple element 'a' mapped by 'e' becomes 'ea'."""
    
    app = QApplication(sys.argv)
    
    # Create scene
    scene = DiagramScene()
    
    # Create objects
    obj_b = Object("B")
    obj_b.setPos(100, 100)
    # Set domain to have simple element a
    obj_b.set_text("a:B")
    
    obj_c = Object("C") 
    obj_c.setPos(300, 100)
    
    scene.addItem(obj_b)
    scene.addItem(obj_c)
    
    # Create arrow e: B -> C
    arrow = Arrow(obj_b, obj_c)
    arrow.set_text("e")
    scene.addItem(arrow)
    
    print("\nTest: Mapping simple element a by function e")
    print(f"Before mapping - Domain: {obj_b.get_display_text()}")
    print(f"Before mapping - Codomain: {obj_c.get_display_text()}")
    
    # Apply MapElement proof step
    proof_step = MapElementProofStep(scene, [], [arrow])
    
    try:
        proof_step.apply()
        
        print(f"After mapping - Domain: {obj_b.get_display_text()}")
        print(f"After mapping - Codomain: {obj_c.get_display_text()}")
        
        # Check if the result is correct
        codomain_text = obj_c.get_display_text()
        expected_pattern = "ea"
        
        if expected_pattern in codomain_text:
            print(f"✅ SUCCESS: Found correct pattern '{expected_pattern}' in result")
            return True
        else:
            print(f"❌ FAILURE: Expected pattern '{expected_pattern}' not found")
            print(f"   Got result: {codomain_text}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR during mapping: {e}")
        return False

if __name__ == "__main__":
    success1 = test_kernel_map_element()
    success2 = test_simple_element_mapping()
    
    if success1 and success2:
        print("\n🎉 All tests passed!")
    else:
        print("\n💥 Some tests failed!")
    
    sys.exit(0 if (success1 and success2) else 1)