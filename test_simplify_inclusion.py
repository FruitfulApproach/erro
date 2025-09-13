#!/usr/bin/env python3
"""
Test SimplifyInclusionProofStep to ensure it correctly simplifies fa:X to a:X when f is an inclusion.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from widget.diagram_scene import DiagramScene
from widget.object_node import Object
from widget.arrow import Arrow
from core.proof_step import SimplifyInclusionProofStep

def test_pattern_recognition():
    """Test that the proof step recognizes inclusion patterns correctly."""
    
    test_cases = [
        ("fa:A", ["f"], True, "Simple inclusion application"),
        ("ga,b:B", ["g"], True, "Inclusion with other element"),
        ("hα:C", ["h"], True, "Greek letter element"),
        ("fx,gy:D", ["f", "g"], True, "Multiple inclusions"),
        ("a:E", ["f"], False, "No inclusion application"),
        ("f(a):F", ["f"], False, "Function composition, not inclusion"),
        ("fa:G", ["h"], False, "Function f exists but h is inclusion"),
    ]
    
    print("Testing inclusion pattern recognition:")
    all_passed = True
    
    for text, inclusions, expected, description in test_cases:
        result = SimplifyInclusionProofStep._contains_inclusion_applications(text, inclusions)
        status = "✅" if result == expected else "❌"
        print(f"  {status} {description}: '{text}' with inclusions {inclusions} → {result} (expected {expected})")
        if result != expected:
            all_passed = False
    
    return all_passed

def test_inclusion_applications_finding():
    """Test finding and extracting inclusion applications."""
    
    test_cases = [
        ("fa:A", ["f"], [{"function": "f", "element": "a"}]),
        ("fαβ:B", ["f"], [{"function": "f", "element": "αβ"}]),
        ("ga,fb:C", ["f", "g"], [{"function": "g", "element": "a"}, {"function": "f", "element": "b"}]),
        ("hx,other,iy:D", ["h", "i"], [{"function": "h", "element": "x"}, {"function": "i", "element": "y"}]),
        ("normal:E", ["f"], []),
    ]
    
    print("\nTesting inclusion applications finding:")
    all_passed = True
    
    for text, inclusions, expected in test_cases:
        applications = SimplifyInclusionProofStep._find_inclusion_applications(text, inclusions)
        
        # Check that we found the expected number of applications
        if len(applications) != len(expected):
            print(f"  ❌ '{text}' found {len(applications)} applications, expected {len(expected)}")
            all_passed = False
            continue
        
        # Check each application
        success = True
        for i, app in enumerate(applications):
            exp = expected[i]
            if app['function'] != exp['function'] or app['element'] != exp['element']:
                print(f"  ❌ Application {i}: got function='{app['function']}' element='{app['element']}', expected function='{exp['function']}' element='{exp['element']}'")
                success = False
        
        if success:
            print(f"  ✅ '{text}' → found {len(applications)} applications correctly")
        else:
            all_passed = False
    
    return all_passed

def test_is_applicable():
    """Test the is_applicable method with different scenarios."""
    
    app = QApplication(sys.argv)
    
    # Create scene with inclusion arrows
    scene = DiagramScene()
    
    # Create objects
    obj1 = Object("A")
    obj1.set_text("fa:A")
    scene.addItem(obj1)
    
    obj2 = Object("B")  
    obj2.set_text("normal:B")
    scene.addItem(obj2)
    
    # Create inclusion arrow
    inclusion_arrow = Arrow(obj1, obj2)
    inclusion_arrow.set_text("f")
    inclusion_arrow._is_inclusion = True
    scene.addItem(inclusion_arrow)
    
    # Create non-inclusion arrow
    normal_arrow = Arrow(obj2, obj1)
    normal_arrow.set_text("g")
    normal_arrow._is_inclusion = False
    scene.addItem(normal_arrow)
    
    print("\nTesting is_applicable:")
    
    # Test with object that has inclusion application
    result1 = SimplifyInclusionProofStep.is_applicable([obj1], [], scene)
    print(f"  ✅ Object with 'fa:A' and f is inclusion: {result1} (should be True)")
    
    # Test with object without inclusion application
    result2 = SimplifyInclusionProofStep.is_applicable([obj2], [], scene)
    print(f"  ✅ Object with 'normal:B': {result2} (should be False)")
    
    # Test with no objects selected
    result3 = SimplifyInclusionProofStep.is_applicable([], [], scene)
    print(f"  ✅ No objects selected: {result3} (should be False)")
    
    # Test with multiple objects selected  
    result4 = SimplifyInclusionProofStep.is_applicable([obj1, obj2], [], scene)
    print(f"  ✅ Multiple objects selected: {result4} (should be False)")
    
    return result1 and not result2 and not result3 and not result4

def test_button_text():
    """Test that the button text correctly shows the inclusion to be simplified."""
    
    app = QApplication(sys.argv)
    
    # Create scene with inclusion arrow
    scene = DiagramScene()
    
    obj = Object("A")
    obj.set_text("fa:A")
    scene.addItem(obj)
    
    obj2 = Object("B")
    scene.addItem(obj2)
    
    # Create inclusion arrow
    arrow = Arrow(obj, obj2)
    arrow.set_text("f")
    arrow._is_inclusion = True
    scene.addItem(arrow)
    
    button_text = SimplifyInclusionProofStep.button_text([obj], [])
    expected = "Remove inclusion f: fa → a"
    
    print(f"\nButton text test:")
    print(f"Input: fa:A with inclusion f")
    print(f"Button text: '{button_text}'")
    print(f"Expected: '{expected}'")
    
    if button_text == expected:
        print("✅ SUCCESS: Button text correct")
        return True
    else:
        print("❌ FAILURE: Button text incorrect")
        return False

def test_apply_single_inclusion():
    """Test applying the proof step to simplify a single inclusion."""
    
    app = QApplication(sys.argv)
    
    # Create scene with inclusion arrow
    scene = DiagramScene()
    
    obj = Object("A")
    obj.set_text("fa:A")
    scene.addItem(obj)
    
    obj2 = Object("B")
    scene.addItem(obj2)
    
    # Create inclusion arrow
    arrow = Arrow(obj, obj2)
    arrow.set_text("f")
    arrow._is_inclusion = True
    scene.addItem(arrow)
    
    print("\nTest: Apply single inclusion simplification")
    print(f"Before: {obj.get_display_text()}")
    
    # Apply proof step
    proof_step = SimplifyInclusionProofStep(scene, [obj], [])
    proof_step.apply()
    
    print(f"After: {obj.get_display_text()}")
    
    if obj.get_display_text() == "a:A":
        print("✅ SUCCESS: Single inclusion simplified correctly")
        return True
    else:
        print("❌ FAILURE: Single inclusion not simplified correctly")
        return False

def test_apply_multiple_inclusions():
    """Test applying the proof step to simplify multiple inclusions."""
    
    app = QApplication(sys.argv)
    
    # Create scene with multiple inclusion arrows
    scene = DiagramScene()
    
    obj = Object("A")
    obj.set_text("fx,gy,hz:A")
    scene.addItem(obj)
    
    obj2 = Object("B")
    obj3 = Object("C") 
    obj4 = Object("D")
    scene.addItem(obj2)
    scene.addItem(obj3)
    scene.addItem(obj4)
    
    # Create inclusion arrows
    arrow1 = Arrow(obj, obj2)
    arrow1.set_text("f")
    arrow1._is_inclusion = True
    scene.addItem(arrow1)
    
    arrow2 = Arrow(obj, obj3)
    arrow2.set_text("g")
    arrow2._is_inclusion = True
    scene.addItem(arrow2)
    
    # Regular arrow (not inclusion)
    arrow3 = Arrow(obj, obj4)
    arrow3.set_text("h")
    arrow3._is_inclusion = False
    scene.addItem(arrow3)
    
    print("\nTest: Apply multiple inclusion simplifications")
    print(f"Before: {obj.get_display_text()}")
    
    # Apply proof step
    proof_step = SimplifyInclusionProofStep(scene, [obj], [])
    proof_step.apply()
    
    print(f"After: {obj.get_display_text()}")
    
    # Should simplify f and g (inclusions) but not h (regular arrow)
    if obj.get_display_text() == "x,y,hz:A":
        print("✅ SUCCESS: Multiple inclusions simplified correctly")
        return True
    else:
        print("❌ FAILURE: Multiple inclusions not simplified correctly")
        return False

def test_undo():
    """Test that the proof step can be undone correctly."""
    
    app = QApplication(sys.argv)
    
    # Create scene with inclusion arrow
    scene = DiagramScene()
    
    obj = Object("A")
    original_text = "fa,other:A"
    obj.set_text(original_text)
    scene.addItem(obj)
    
    obj2 = Object("B")
    scene.addItem(obj2)
    
    # Create inclusion arrow
    arrow = Arrow(obj, obj2)
    arrow.set_text("f")
    arrow._is_inclusion = True
    scene.addItem(arrow)
    
    print("\nTest: Undo inclusion simplification")
    print(f"Original: {obj.get_display_text()}")
    
    # Apply proof step
    proof_step = SimplifyInclusionProofStep(scene, [obj], [])
    proof_step.apply()
    
    print(f"After apply: {obj.get_display_text()}")
    
    # Undo
    proof_step.unapply()
    
    print(f"After undo: {obj.get_display_text()}")
    
    if obj.get_display_text() == original_text:
        print("✅ SUCCESS: Undo restored original text")
        return True
    else:
        print("❌ FAILURE: Undo did not restore original text")
        return False

if __name__ == "__main__":
    success1 = test_pattern_recognition()
    success2 = test_inclusion_applications_finding()
    success3 = test_is_applicable()
    success4 = test_button_text()
    success5 = test_apply_single_inclusion()
    success6 = test_apply_multiple_inclusions()
    success7 = test_undo()
    
    if all([success1, success2, success3, success4, success5, success6, success7]):
        print("\n🎉 All simplify inclusion tests passed!")
    else:
        print("\n💥 Some simplify inclusion tests failed!")
    
    sys.exit(0 if all([success1, success2, success3, success4, success5, success6, success7]) else 1)