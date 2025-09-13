"""
Pythom DAG Diagram Editor

A PyQt6-based application for creating and editing Directed Acyclic Graph (DAG) diagrams.

Package structure:
- node.py: Base Node class (QGraphicsObject)
- object_node.py: Object class inheriting from Node
- arrow.py: Arrow class inheriting from Node for connections
- diagram_scene.py: DiagramScene class (QGraphicsScene subclass)
- diagram_view.py: DiagramView class (QGraphicsView subclass)
- main_window.py: MainWindow class with UI
- main.py: Application entry point
"""

__version__ = "1.0.0"
__author__ = "Pythom Developer"

# Import main classes for easy access
from widget.node import Node
from widget.object_node import Object
from widget.arrow import Arrow
from widget.diagram_scene import DiagramScene
from widget.diagram_view import DiagramView
from widget.main_window import MainWindow

__all__ = [
    'Node',
    'Object', 
    'Arrow',
    'DiagramScene',
    'DiagramView',
    'MainWindow'
]
