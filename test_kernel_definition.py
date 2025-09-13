#!/usr/bin/env python3
"""
Test KernelDefinitionProofStep to ensure it moves elements from fx=0 to Ker f correctly.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from widget.diagram_scene import DiagramScene
from widget.object_node import Object
from core.proof_step import KernelDefinitionProofStep

def test_kernel_definition_pattern_recognition():
    """Test that the proof step recognizes fx=0 patterns correctly."""
    
    test_cases = [
        ("fα=0:A", True, "Simple function application fα=0"),
        ("gβ=0,other:B", True, "Function application with other elements"),
        ("hxy=0:C", True, "Multi-character element"),
        ("f=0:D", False, "No element (just function)"),
        ("α=0:E", False, "No function (just element)"),
        ("fa=b:F", False, "No zero equality"),
        ("simple:G", False, "No pattern at all"),
    ]
    
    print("Testing kernel definition pattern recognition:")
    all_passed = True
    
    for text, expected, description in test_cases:
        result = KernelDefinitionProofStep._contains_kernel_definition_pattern(text)
        status = "✅" if result == expected else "❌"
        print(f"  {status} {description}: '{text}' → {result} (expected {expected})")
        if result != expected:
            all_passed = False
    
    return all_passed

def test_kernel_definition_info_extraction():
    """Test extraction of function and element from fx=0 patterns."""
    
    test_cases = [
        ("fα=0:A", "f", "α"),
        ("gβγ=0:B", "g", "βγ"),
        ("hxyz=0:C", "h", "xyz"),
        ("simple:D", None, None),
    ]
    
    print("\nTesting kernel definition info extraction:")
    all_passed = True
    
    for text, expected_func, expected_elem in test_cases:
        func, elem = KernelDefinitionProofStep._extract_kernel_definition_info(text)
        
        func_ok = func == expected_func
        elem_ok = elem == expected_elem
        
        status = "✅" if func_ok and elem_ok else "❌"
        print(f"  {status} '{text}' → func: '{func}' (exp: '{expected_func}'), elem: '{elem}' (exp: '{expected_elem}')")
        
        if not (func_ok and elem_ok):
            all_passed = False
    
    return all_passed

def test_kernel_definition_application_new_kernel():
    """Test applying kernel definition when kernel node doesn't exist."""
    
    app = QApplication(sys.argv)
    
    # Create scene and enable abelian category
    scene = DiagramScene()
    scene._is_abelian_category = True
    
    # Create object with fx=0
    obj = Object("A")
    obj.setPos(100, 100)
    obj.set_text("fα=0:A")
    scene.addItem(obj)
    
    print("\nTest 1: Creating new kernel node")
    print(f"Before: {obj.get_display_text()}")
    print(f"Objects in scene: {len([item for item in scene.items() if hasattr(item, 'get_text') and not hasattr(item, 'get_source')])}")
    
    # Check if proof step is applicable
    if not KernelDefinitionProofStep.is_applicable([obj], []):
        print("❌ FAILURE: Proof step not applicable")
        return False
    
    # Get button text
    button_text = KernelDefinitionProofStep.button_text([obj], [])
    print(f"Button text: {button_text}")
    
    # Apply proof step
    proof_step = KernelDefinitionProofStep(scene, [obj], [])
    proof_step.apply()
    
    # Check results
    print(f"After - Original node: {obj.get_display_text()}")
    
    # Find all objects in scene
    objects = [item for item in scene.items() if hasattr(item, 'get_text') and not hasattr(item, 'get_source')]
    print(f"Objects in scene after: {len(objects)}")
    
    # Look for kernel node
    kernel_node = None
    for item in objects:
        if "Ker f" in item.get_display_text():
            kernel_node = item
            break
    
    if kernel_node:
        print(f"Kernel node created: {kernel_node.get_display_text()}")
        
        # Check if original node no longer has fα=0
        if "fα=0" not in obj.get_display_text():
            print("✅ SUCCESS: Element removed from original node")
        else:
            print("❌ FAILURE: Element not removed from original node")
            return False
        
        # Check if kernel node has α
        if "α:" in kernel_node.get_display_text():
            print("✅ SUCCESS: Element added to kernel node")
            return True
        else:
            print("❌ FAILURE: Element not found in kernel node")
            return False
    else:
        print("❌ FAILURE: Kernel node not created")
        return False

def test_kernel_definition_application_existing_kernel():
    """Test applying kernel definition when kernel node already exists."""
    
    app = QApplication(sys.argv)
    
    # Create scene and enable abelian category
    scene = DiagramScene()
    scene._is_abelian_category = True
    
    # Create object with fx=0
    obj = Object("A")
    obj.setPos(100, 100)
    obj.set_text("fβ=0:A")
    scene.addItem(obj)
    
    # Create existing kernel node
    kernel_obj = Object("Ker f")
    kernel_obj.setPos(200, 100)
    kernel_obj.set_text("γ:Ker f")  # Already has element γ
    scene.addItem(kernel_obj)
    
    print("\nTest 2: Using existing kernel node")
    print(f"Before - Original: {obj.get_display_text()}")
    print(f"Before - Kernel: {kernel_obj.get_display_text()}")
    
    # Apply proof step
    proof_step = KernelDefinitionProofStep(scene, [obj], [])
    proof_step.apply()
    
    print(f"After - Original: {obj.get_display_text()}")
    print(f"After - Kernel: {kernel_obj.get_display_text()}")
    
    # Check results
    if "fβ=0" not in obj.get_display_text() and "γ,β:Ker f" in kernel_obj.get_display_text():
        print("✅ SUCCESS: Element moved to existing kernel node")
        return True
    else:
        print("❌ FAILURE: Element not properly moved to existing kernel node")
        return False

def test_button_text():
    """Test that the button text correctly identifies the kernel definition."""
    
    app = QApplication(sys.argv)
    
    obj = Object("Test")
    obj.set_text("fα=0:A")
    
    button_text = KernelDefinitionProofStep.button_text([obj], [])
    expected = "Move α to Ker f"
    
    print(f"\nButton text test:")
    print(f"Input: fα=0:A")
    print(f"Button text: '{button_text}'")
    print(f"Expected: '{expected}'")
    
    if button_text == expected:
        print("✅ SUCCESS: Button text correct")
        return True
    else:
        print("❌ FAILURE: Button text incorrect")
        return False

if __name__ == "__main__":
    success1 = test_kernel_definition_pattern_recognition()
    success2 = test_kernel_definition_info_extraction()
    success3 = test_kernel_definition_application_new_kernel()
    success4 = test_kernel_definition_application_existing_kernel()
    success5 = test_button_text()
    
    if success1 and success2 and success3 and success4 and success5:
        print("\n🎉 All kernel definition tests passed!")
    else:
        print("\n💥 Some kernel definition tests failed!")
    
    sys.exit(0 if all([success1, success2, success3, success4, success5]) else 1)