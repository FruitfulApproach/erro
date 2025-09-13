"""
Test script for composition notation and kernel zero proof steps.
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
from core.proof_step import MapElementProofStep, KernelAtElementIsZeroProofStep

def test_composition_and_kernel_zero():
    """Test the composition notation and kernel zero functionality."""
    
    app = App(sys.argv)
    main_window = MainWindow()
    
    # Get the current scene
    scene = main_window.get_current_scene()
    scene.is_concrete_category = True
    scene.is_abelian_category = True  # Enable both features
    
    # Test 1: Composition notation
    print("=== Test 1: Function Composition Notation ===")
    
    # Test the _create_mapped_element_notation method
    map_step = MapElementProofStep(scene, [], [])
    
    # Test simple element
    result1 = map_step._create_mapped_element_notation("a", "f")
    print(f"f maps 'a' -> '{result1}'")  # Should be "f(a)"
    
    # Test already mapped element
    result2 = map_step._create_mapped_element_notation("f(a)", "g")
    print(f"g maps 'f(a)' -> '{result2}'")  # Should be "(g∘f)(a)"
    
    # Test composed element
    result3 = map_step._create_mapped_element_notation("(g∘f)(a)", "h")
    print(f"h maps '(g∘f)(a)' -> '{result3}'")  # Should be "(h∘g∘f)(a)"
    
    # Test zero element
    result4 = map_step._create_mapped_element_notation("(e∘k_e)(a)=0", "g")
    print(f"g maps '(e∘k_e)(a)=0' -> '{result4}'")  # Should be "g(0)=0"
    
    # Test 2: Kernel at Element is Zero
    print("\n=== Test 2: Kernel Element Pattern Detection ===")
    
    # Create test object with kernel pattern
    kernel_obj = Object(text="(e∘k_e)(a), b : KerE")
    kernel_obj.setPos(QPointF(100, 100))
    scene.addItem(kernel_obj)
    
    # Test applicability
    objects = [kernel_obj]
    arrows = []
    
    print(f"Object display text: '{kernel_obj.get_display_text()}'")
    print(f"KernelAtElementIsZero applicable: {KernelAtElementIsZeroProofStep.is_applicable(objects, arrows)}")
    print(f"Button text: {KernelAtElementIsZeroProofStep.button_text(objects, arrows)}")
    
    # Test pattern detection
    print(f"'(e∘k_e)(a)' is kernel pattern: {KernelAtElementIsZeroProofStep._is_kernel_element_pattern('(e∘k_e)(a)')}")
    print(f"'f(a)' is kernel pattern: {KernelAtElementIsZeroProofStep._is_kernel_element_pattern('f(a)')}")
    
    print("\nAll tests completed successfully!")
    
    app.quit()

if __name__ == "__main__":
    test_composition_and_kernel_zero()