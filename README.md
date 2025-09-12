# Pythom - DAG Diagram Editor

A PyQt6-based application for creating and editing Directed Acyclic Graph (DAG) diagrams.

## Features

- **Node-based Architecture**: Built with a clean class hierarchy
  - `Node(QGraphicsObject)` - Base class for all diagram elements
  - `Object(Node)` - Represents data/process nodes in the DAG
  - `Arrow(Node)` - Represents connections between objects

- **Custom Scene and View**:
  - `DiagramScene(QGraphicsScene)` - Custom scene with grid and object placement
  - `DiagramView(QGraphicsView)` - Enhanced view with zoom and pan capabilities

- **Interactive Features**:
  - Double-click canvas to place objects (snaps to 100x100 grid)
  - Drag objects to move them (snaps to grid)
  - Zoom in/out with mouse wheel or keyboard shortcuts
  - Pan with middle mouse button or keyboard
  - Selection highlighting

## Usage

Run the application:
```bash
python main.py
```

### Controls

- **Double-click**: Add a new object to the canvas
- **Mouse wheel**: Zoom in/out
- **Middle mouse button**: Pan the view
- **Drag**: Move selected objects
- **Ctrl+Plus/Minus**: Zoom in/out
- **Ctrl+0**: Reset zoom to 100%
- **Ctrl+F**: Fit all objects in view

## Requirements

- Python 3.8+
- PyQt6

Install PyQt6:
```bash
pip install PyQt6
```

## Project Structure

```
HomPy/
├── main.py              # Application entry point
├── main_window.py       # Main window with menus and toolbar
├── diagram_scene.py     # Custom QGraphicsScene
├── diagram_view.py      # Custom QGraphicsView with zoom/pan
├── node.py              # Base Node class
├── object_node.py       # Object node implementation
├── arrow.py             # Arrow node for connections
├── __init__.py          # Package initialization
└── README.md            # This file
```

## Class Hierarchy

```
QGraphicsObject
└── Node (base class)
    ├── Object (rounded rectangle nodes)
    └── Arrow (connection arrows)

QGraphicsScene
└── DiagramScene (grid background, object placement)

QGraphicsView  
└── DiagramView (zoom, pan, keyboard shortcuts)

QMainWindow
└── MainWindow (menus, toolbar, status bar)
```

## Future Enhancements

- Arrow creation by connecting objects
- Object property editing
- Save/load diagram files
- Export to image formats
- Undo/redo functionality
- Object types and styling
- Connection validation for DAG constraints
