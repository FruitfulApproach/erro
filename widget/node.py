"""
Base Node class for DAG diagram elements.
"""
from PyQt6.QtWidgets import QGraphicsObject, QGraphicsItem
from PyQt6.QtCore import QRectF, pyqtSignal
from PyQt6.QtGui import QPen, QBrush, QColor


class Node(QGraphicsObject):
    """Base class for all diagram nodes."""
    
    # Signal emitted when node is moved
    node_moved = pyqtSignal(object)
    
    # Signal emitted when node name/text changes
    name_changed = pyqtSignal(str)  # emits the new name
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        
        # Default properties - square for grid alignment
        self._width = 80
        self._height = 80
        self._pen = QPen(QColor(0, 0, 0), 2)
        self._brush = QBrush(QColor(200, 200, 200))
        
        # Highlighting for cycle detection
        self._highlight_color = None
        self._original_pen = self._pen
        self._original_brush = self._brush
        
        # For tracking moves
        self._start_position = None
        self._is_moving = False
        
    def boundingRect(self):
        """Return the bounding rectangle of the node."""
        return QRectF(0, 0, self._width, self._height)
    
    def itemChange(self, change, value):
        """Handle item changes, particularly position changes."""
        from PyQt6.QtCore import QPointF
        
    def itemChange(self, change, value):
        """Handle item changes, particularly position changes."""
        from PyQt6.QtCore import QPointF
        
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            # Snap to grid intersections (simple grid snapping)
            new_pos = value
            grid_size = 150  # Updated to match scene grid size
            
            # Find the nearest grid intersection
            grid_x = round(new_pos.x() / grid_size) * grid_size
            grid_y = round(new_pos.y() / grid_size) * grid_size
            
            snapped_pos = QPointF(grid_x, grid_y)
            
            # Check if this position is occupied by another object (only for Object nodes)
            if hasattr(self, 'get_text') and self.scene():  # This identifies Object nodes
                from .object_node import Object
                for item in self.scene().items():
                    if isinstance(item, Object) and item != self:
                        item_pos = item.pos()
                        # Calculate snapped position for existing item
                        item_grid_x = round(item_pos.x() / grid_size) * grid_size
                        item_grid_y = round(item_pos.y() / grid_size) * grid_size
                        
                        if item_grid_x == grid_x and item_grid_y == grid_y:
                            # Position is occupied, return current position (block the move)
                            return self.pos()
            
            return snapped_pos
        elif change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            self.node_moved.emit(self)
            
            # Update self-loops when an object moves (only for Object nodes)
            if hasattr(self, 'get_text') and self.scene():
                # Import here to avoid circular imports
                from .arrow import Arrow
                Arrow.update_self_loops_for_node(self)
        
        return super().itemChange(change, value)
    
    def width(self):
        return self._width
    
    def height(self):
        return self._height
    
    def set_size(self, width, height):
        """Set the size of the node."""
        self.prepareGeometryChange()
        self._width = width
        self._height = height
        self.update()
    
    def set_pen(self, pen):
        """Set the pen for drawing the node."""
        self._pen = pen
        self.update()
    
    def set_brush(self, brush):
        """Set the brush for filling the node."""
        self._brush = brush
        self.update()
    
    def mousePressEvent(self, event):
        """Handle mouse press events to start tracking moves."""
        from PyQt6.QtCore import Qt
        # Accept any mouse button for movement, not just left button
        self._start_position = self.pos()
        self._is_moving = True
        self._move_button = event.button()  # Remember which button started the move
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release events to complete move tracking."""
        from PyQt6.QtCore import Qt
        print(f"Node mouseReleaseEvent: button={event.button()}, pos={event.pos()}")
        print(f"Current position: {self.pos()}, start position: {self._start_position}")
        print(f"Has get_text: {hasattr(self, 'get_text')}")
        
        if (event.button() == Qt.MouseButton.LeftButton and 
            self._is_moving and 
            self._start_position is not None and 
            hasattr(self, 'get_text')):  # Only for Object nodes, not arrows
            
            end_position = self.pos()
            print(f"End position: {end_position}")
            if self._start_position != end_position:
                print("Creating MoveObject command...")
                # Create move command
                from core.undo_commands import MoveObject
                from PyQt6.QtWidgets import QApplication
                
                command = MoveObject(self, self._start_position, end_position)
                app = QApplication.instance()
                print(f"App has undo_stack: {hasattr(app, 'undo_stack')}")
                app.undo_stack.push(command)
                print("Move command pushed to undo stack")
            else:
                print("No position change detected")
        
        self._is_moving = False
        self._start_position = None
        super().mouseReleaseEvent(event)
    
    def set_highlight_color(self, color):
        """Set highlight color for cycle detection."""
        self._highlight_color = color
        if color:
            # Create highlighted pen and brush
            self._pen = QPen(QColor(255, 0, 0), 3)  # Red border
            self._brush = QBrush(color)  # Highlighted fill
        else:
            # Restore original colors
            self._pen = self._original_pen
            self._brush = self._original_brush
        self.update()
    
    def clear_highlight_color(self):
        """Clear highlight color."""
        self.set_highlight_color(None)
