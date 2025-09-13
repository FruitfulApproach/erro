#!/usr/bin/env python3
"""
Test script to verify that arrow inclusion property is properly serialized and restored.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from widget.diagram_scene import DiagramScene
from widget.object_node import Object
from widget.arrow import Arrow
from core.session_manager import SessionManager

def test_inclusion_serialization():
    """Test that arrow inclusion property survives save/load cycle."""
    
    app = QApplication(sys.argv)
    
    # Create original scene
    scene = DiagramScene()
    
    # Create objects
    obj_a = Object("A")
    obj_a.setPos(100, 100)
    obj_b = Object("B") 
    obj_b.setPos(300, 100)
    
    scene.addItem(obj_a)
    scene.addItem(obj_b)
    
    # Create arrow
    arrow = Arrow(obj_a, obj_b)
    arrow.set_text("f")
    
    # Set it as inclusion (hook tail)
    arrow._is_inclusion = True
    print(f"Original arrow inclusion status: {arrow._is_inclusion}")
    
    scene.addItem(arrow)
    
    # Serialize the scene
    session_manager = SessionManager()
    scene_data = session_manager.serialize_diagram_scene(scene)
    
    print("Serialized scene data:")
    for arrow_data in scene_data.get('arrows', []):
        print(f"  Arrow '{arrow_data['text']}' is_inclusion: {arrow_data.get('is_inclusion', 'NOT FOUND')}")
    
    # Create new scene and restore
    new_scene = DiagramScene()
    success = session_manager.restore_diagram_scene(new_scene, scene_data)
    
    if not success:
        print("❌ Failed to restore scene")
        return False
    
    # Check if inclusion property was restored
    arrows_in_new_scene = [item for item in new_scene.items() if hasattr(item, 'get_source')]
    
    if not arrows_in_new_scene:
        print("❌ No arrows found in restored scene")
        return False
    
    restored_arrow = arrows_in_new_scene[0]
    print(f"Restored arrow inclusion status: {restored_arrow._is_inclusion}")
    
    if restored_arrow._is_inclusion:
        print("✅ SUCCESS: Arrow inclusion property was properly serialized and restored!")
        return True
    else:
        print("❌ FAILURE: Arrow inclusion property was lost during serialization/restoration")
        return False

if __name__ == "__main__":
    success = test_inclusion_serialization()
    sys.exit(0 if success else 1)