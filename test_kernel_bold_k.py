"""
Test that kernel objects are created with bold            kernel_name = kernel_step.kernel_object.get_text()
            print(f"Kernel object name: '{kernel_name}'")
            print(f"Expected format: '𝐊𝐞𝐫 f'")
            print(f"Correct format: {kernel_name == '𝐊𝐞𝐫 f'}")ormat.
"""

import sys
sys.path.append('.')

from PyQt6.QtCore import QPointF
from PyQt6.QtWidgets import QApplication
from widget.object_node import Object
from widget.arrow import Arrow
from widget.diagram_scene import DiagramScene
from core.proof_step import TakeKernelProofStep

def test_kernel_bold_k():
    print("Testing Kernel Generation with Bold K:")
    print("=" * 40)
    
    # Create QApplication instance
    app = QApplication.instance() or QApplication(sys.argv)
    
    # Create scene and enable abelian category
    scene = DiagramScene()
    scene._is_abelian_category = True
    
    # Create objects and arrow
    obj1 = Object("A")
    obj1.setPos(QPointF(0, 0))
    scene.addItem(obj1)
    
    obj2 = Object("B")  
    obj2.setPos(QPointF(150, 0))
    scene.addItem(obj2)
    
    # Create arrow f: A -> B
    arrow = Arrow(obj1, obj2, "f")
    scene.addItem(arrow)
    
    print(f"Original arrow: {arrow.get_text()}")
    
    # Test if TakeKernelProofStep is applicable
    is_applicable = TakeKernelProofStep.is_applicable([], [arrow])
    print(f"Is applicable: {is_applicable}")
    
    if is_applicable:
        # Apply the kernel proof step
        kernel_step = TakeKernelProofStep(scene, [], [arrow])
        kernel_step.apply()
        
        # Check if kernel object was created
        if kernel_step.kernel_object:
            kernel_name = kernel_step.kernel_object.get_text()
            print(f"Kernel object name: '{kernel_name}'")
            print(f"Expected format: '�er f'")
            print(f"Correct format: {kernel_name == '�er f'}")
            
            # Check if kernel arrow was created
            if kernel_step.kernel_arrow:
                kernel_arrow_name = kernel_step.kernel_arrow.get_text()
                print(f"Kernel arrow name: '{kernel_arrow_name}'")
                print(f"Expected format: '𝐤(f)'")
                print(f"Correct format: {kernel_arrow_name == '𝐤(f)'}")
        else:
            print("No kernel object was created")
    
    print("\n" + "=" * 40)
    print("Kernel bold K test completed!")

if __name__ == "__main__":
    test_kernel_bold_k()