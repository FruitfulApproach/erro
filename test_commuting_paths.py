#!/usr/bin/env python3
"""
Test CommutingPathsProofStep to ensure it recognizes and equates commuting paths.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from widget.diagram_scene import DiagramScene
from widget.object_node import Object
from core.proof_step import CommutingPathsProofStep

def test_commuting_paths_recognition():
    """Test that the proof step recognizes commuting paths correctly."""
    
    test_cases = [
        ("cba,fga:C", True, "Two different paths to element 'a'"),
        ("xyz,abc:D", False, "Different end elements"),
        ("fa,fb:A", False, "Same prefix, different elements"),
        ("gha,kja,mna:B", True, "Three different paths to element 'a'"),
        ("simple:E", False, "Single element, no paths"),
        ("a=b:F", False, "Equality, not paths"),
        ("f(a):G", False, "Parentheses notation"),
    ]
    
    print("Testing commuting paths recognition:")
    all_passed = True
    
    for text, expected, description in test_cases:
        result = CommutingPathsProofStep._has_commuting_paths(text)
        status = "✅" if result == expected else "❌"
        print(f"  {status} {description}: '{text}' → {result} (expected {expected})")
        if result != expected:
            all_passed = False
    
    return all_passed

def test_path_parsing():
    """Test path prefix and suffix extraction."""
    
    test_cases = [
        ("cba", "cb", "a"),
        ("fga", "fg", "a"),
        ("xyz", "xy", "z"),
        ("a", "", "a"),
        ("f=g", None, None),  # Equality should be skipped
    ]
    
    print("\nTesting path parsing:")
    all_passed = True
    
    for path, expected_prefix, expected_suffix in test_cases:
        suffix = CommutingPathsProofStep._extract_element_suffix(path)
        prefix = CommutingPathsProofStep._extract_path_prefix(path)
        
        suffix_ok = suffix == expected_suffix
        prefix_ok = prefix == expected_prefix
        
        status = "✅" if suffix_ok and prefix_ok else "❌"
        print(f"  {status} '{path}' → prefix: '{prefix}' (exp: '{expected_prefix}'), suffix: '{suffix}' (exp: '{expected_suffix}')")
        
        if not (suffix_ok and prefix_ok):
            all_passed = False
    
    return all_passed

def test_path_equalities_creation():
    """Test that commuting paths are correctly equated."""
    
    app = QApplication(sys.argv)
    
    # Create scene
    scene = DiagramScene()
    
    # Test case 1: Simple commuting paths
    obj1 = Object("A")
    obj1.setPos(100, 100)
    obj1.set_text("cba,fga:A")  # Two paths to element 'a'
    scene.addItem(obj1)
    
    print("\nTest 1: Simple commuting paths cba,fga")
    print(f"Before: {obj1.get_display_text()}")
    
    # Check if proof step is applicable
    if not CommutingPathsProofStep.is_applicable([obj1], []):
        print("❌ FAILURE: Proof step not applicable")
        return False
    
    # Apply proof step
    proof_step = CommutingPathsProofStep(scene, [obj1], [])
    proof_step.apply()
    
    result1 = obj1.get_display_text()
    print(f"After: {result1}")
    
    if "cba=fga" in result1:
        print("✅ SUCCESS: Paths correctly equated")
        success1 = True
    else:
        print(f"❌ FAILURE: Expected 'cba=fga' in result")
        success1 = False
    
    # Test case 2: Multiple paths to same element
    obj2 = Object("B")
    obj2.setPos(300, 100)
    obj2.set_text("gha,kja,mna:B")  # Three paths to element 'a'
    scene.addItem(obj2)
    
    print("\nTest 2: Multiple paths gha,kja,mna")
    print(f"Before: {obj2.get_display_text()}")
    
    proof_step2 = CommutingPathsProofStep(scene, [obj2], [])
    proof_step2.apply()
    
    result2 = obj2.get_display_text()
    print(f"After: {result2}")
    
    # Should create equality with all three paths
    if "gha=kja=mna" in result2:
        print("✅ SUCCESS: Multiple paths correctly equated")
        success2 = True
    else:
        print(f"❌ FAILURE: Expected 'gha=kja=mna' in result")
        success2 = False
    
    # Test case 3: Mixed paths and other elements
    obj3 = Object("C")
    obj3.setPos(500, 100)
    obj3.set_text("xyz,cba,fga,other:C")  # Two paths to 'a', one path to 'z', one other element
    scene.addItem(obj3)
    
    print("\nTest 3: Mixed paths xyz,cba,fga,other")
    print(f"Before: {obj3.get_display_text()}")
    
    proof_step3 = CommutingPathsProofStep(scene, [obj3], [])
    proof_step3.apply()
    
    result3 = obj3.get_display_text()
    print(f"After: {result3}")
    
    # Should equate paths to 'a' but leave others separate
    if "cba=fga" in result3 and "xyz" in result3 and "other" in result3:
        print("✅ SUCCESS: Mixed paths handled correctly")
        success3 = True
    else:
        print(f"❌ FAILURE: Mixed paths not handled correctly")
        success3 = False
    
    return success1 and success2 and success3

def test_button_text():
    """Test that the button text correctly identifies commuting paths."""
    
    app = QApplication(sys.argv)
    
    obj = Object("Test")
    obj.set_text("cba,fga:A")
    
    button_text = CommutingPathsProofStep.button_text([obj], [])
    print(f"\nButton text test:")
    print(f"Input: cba,fga:A")
    print(f"Button text: '{button_text}'")
    
    if "cba=fga" in button_text and "a" in button_text:
        print("✅ SUCCESS: Button text identifies paths correctly")
        return True
    else:
        print("❌ FAILURE: Button text incorrect")
        return False

if __name__ == "__main__":
    success1 = test_commuting_paths_recognition()
    success2 = test_path_parsing()
    success3 = test_path_equalities_creation()
    success4 = test_button_text()
    
    if success1 and success2 and success3 and success4:
        print("\n🎉 All commuting paths tests passed!")
    else:
        print("\n💥 Some commuting paths tests failed!")
    
    sys.exit(0 if (success1 and success2 and success3 and success4) else 1)