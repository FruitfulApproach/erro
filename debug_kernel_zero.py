#!/usr/bin/env python3
"""
Debug the ApplicationToKernelIsZeroProofStep with the exact failing case.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from widget.diagram_scene import DiagramScene
from widget.object_node import Object
from core.proof_step import ApplicationToKernelIsZeroProofStep

def debug_kernel_zero_issue():
    """Debug the exact issue with g𝐤(g)a:E -> g𝐤(g)=0a:E"""
    
    app = QApplication(sys.argv)
    
    # Create scene and enable abelian category
    scene = DiagramScene()
    scene._is_abelian_category = True
    
    # Create object with the exact failing case (using Unicode alpha)
    obj = Object("E")
    obj.setPos(100, 100)
    obj.set_text("g𝐤(g)α:E")
    scene.addItem(obj)
    
    print("=== DEBUGGING ApplicationToKernelIsZeroProofStep ===")
    print(f"Input: {obj.get_display_text()}")
    
    # Check if proof step recognizes the pattern
    is_applicable = ApplicationToKernelIsZeroProofStep.is_applicable([obj], [])
    print(f"Is applicable: {is_applicable}")
    
    if not is_applicable:
        print("ERROR: Proof step doesn't recognize the pattern!")
        return False
    
    # Get button text
    button_text = ApplicationToKernelIsZeroProofStep.button_text([obj], [])
    print(f"Button text: {button_text}")
    
    # Apply the proof step
    print("\nApplying proof step...")
    proof_step = ApplicationToKernelIsZeroProofStep(scene, [obj], [])
    
    # Debug the internal method directly
    original_text = obj.get_display_text()
    print(f"Original text: {original_text}")
    
    # Test the internal method
    transformed_text = proof_step._mark_kernel_applications_as_zero(original_text)
    print(f"Transformed text (internal method): {transformed_text}")
    
    # Now actually apply the proof step
    proof_step.apply()
    
    final_text = obj.get_display_text()
    print(f"Final text after apply(): {final_text}")
    
    # Check what went wrong
    expected = "g𝐤(g)α=0:E"
    if final_text == expected:
        print("✅ SUCCESS: Correct transformation")
        return True
    else:
        print(f"❌ FAILURE: Expected '{expected}', got '{final_text}'")
        
        # Try to figure out where it went wrong
        if "g𝐤(g)=0a" in final_text:
            print("   Problem: =0 is being inserted in wrong position")
            print("   This suggests regex replacement is not working correctly")
        
        return False

if __name__ == "__main__":
    success = debug_kernel_zero_issue()
    sys.exit(0 if success else 1)