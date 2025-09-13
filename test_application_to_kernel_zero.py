#!/usr/bin/env python3
"""
Test ApplicationToKernelIsZeroProofStep to ensure it recognizes g𝐤(g) patterns and marks them as zero.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from widget.diagram_scene import DiagramScene
from widget.object_node import Object
from core.proof_step import ApplicationToKernelIsZeroProofStep

def test_kernel_application_pattern_recognition():
    """Test that the proof step recognizes various g𝐤(g) patterns."""
    
    test_cases = [
        ("f𝐤(f)a:A", True, "Simple f𝐤(f)a pattern"),
        ("g𝐤(g)xyz:B", True, "Pattern with multiple element chars"),
        ("abc𝐤(abc)x:C", True, "Multi-char function name"),
        ("f𝐤(g)a:A", False, "Mismatched function names"),
        ("fa:A", False, "No kernel pattern"),
        ("𝐤(f)a:A", False, "Kernel without preceding function"),
        ("ef𝐤(f)a,gh𝐤(g)b:X", True, "Multiple patterns in one object"),
    ]
    
    print("Testing pattern recognition:")
    all_passed = True
    
    for text, expected, description in test_cases:
        result = ApplicationToKernelIsZeroProofStep._contains_kernel_application_pattern(text)
        status = "✅" if result == expected else "❌"
        print(f"  {status} {description}: '{text}' → {result} (expected {expected})")
        if result != expected:
            all_passed = False
    
    return all_passed

def test_kernel_application_transformation():
    """Test that the proof step correctly transforms elements to zero."""
    
    app = QApplication(sys.argv)
    
    # Create scene and enable abelian category
    scene = DiagramScene()
    scene._is_abelian_category = True  # Set the private attribute directly
    
    # Test case 1: Simple kernel application
    obj1 = Object("A")
    obj1.setPos(100, 100)
    obj1.set_text("f𝐤(f)a:A")
    scene.addItem(obj1)
    
    print("\nTest 1: Simple kernel application f𝐤(f)a")
    print(f"Before: {obj1.get_display_text()}")
    
    # Check if proof step is applicable
    if not ApplicationToKernelIsZeroProofStep.is_applicable([obj1], []):
        print("❌ FAILURE: Proof step not applicable")
        return False
    
    # Apply proof step
    proof_step = ApplicationToKernelIsZeroProofStep(scene, [obj1], [])
    proof_step.apply()
    
    result1 = obj1.get_display_text()
    print(f"After: {result1}")
    
    expected_pattern = "f𝐤(f)a=0"
    if expected_pattern in result1:
        print("✅ SUCCESS: Correctly marked as zero")
        success1 = True
    else:
        print(f"❌ FAILURE: Expected '{expected_pattern}' in result")
        success1 = False
    
    # Test case 2: Multiple kernel applications
    obj2 = Object("B")
    obj2.setPos(300, 100)
    obj2.set_text("eg𝐤(g)x,fh𝐤(h)y:B")
    scene.addItem(obj2)
    
    print("\nTest 2: Multiple kernel applications eg𝐤(g)x,fh𝐤(h)y")
    print(f"Before: {obj2.get_display_text()}")
    
    # Check if proof step is applicable
    if not ApplicationToKernelIsZeroProofStep.is_applicable([obj2], []):
        print("❌ FAILURE: Proof step not applicable to multiple patterns")
        return False
    
    # Apply proof step
    proof_step2 = ApplicationToKernelIsZeroProofStep(scene, [obj2], [])
    proof_step2.apply()
    
    result2 = obj2.get_display_text()
    print(f"After: {result2}")
    
    # Check that both patterns were transformed
    if "g𝐤(g)x=0" in result2 and "h𝐤(h)y=0" in result2:
        print("✅ SUCCESS: Both kernel applications marked as zero")
        success2 = True
    else:
        print("❌ FAILURE: Not all kernel applications were marked as zero")
        success2 = False
    
    return success1 and success2

def test_button_text():
    """Test that the button text correctly identifies the kernel pattern."""
    
    app = QApplication(sys.argv)
    
    obj = Object("Test")
    obj.set_text("f𝐤(f)a:A")
    
    button_text = ApplicationToKernelIsZeroProofStep.button_text([obj], [])
    expected = "Mark f𝐤(f) = 0"
    
    print(f"\nButton text test:")
    print(f"Input: f𝐤(f)a:A")
    print(f"Button text: '{button_text}'")
    print(f"Expected: '{expected}'")
    
    if button_text == expected:
        print("✅ SUCCESS: Button text correct")
        return True
    else:
        print("❌ FAILURE: Button text incorrect")
        return False

if __name__ == "__main__":
    success1 = test_kernel_application_pattern_recognition()
    success2 = test_kernel_application_transformation()
    success3 = test_button_text()
    
    if success1 and success2 and success3:
        print("\n🎉 All tests passed!")
    else:
        print("\n💥 Some tests failed!")
    
    sys.exit(0 if (success1 and success2 and success3) else 1)