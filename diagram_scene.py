"""
Custom QGraphicsScene for DAG diagrams.
"""
from PyQt6.QtWidgets import QGraphicsScene, QMenu
from PyQt6.QtCore import QRectF, QPointF, pyqtSignal, QTimer
from PyQt6.QtGui import QPen, QColor, QAction, QUndoCommand
from cycle_detector import CycleDetector


class DiagramScene(QGraphicsScene):
    """Custom graphics scene for DAG diagrams."""
    
    # Signal emitted when an object is added to the scene
    object_added = pyqtSignal(object)
    
    # Signal emitted when an object is added to the scene
    object_added = pyqtSignal(object)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Set scene size
        self.setSceneRect(-2000, -2000, 4000, 4000)
        
        # Grid properties
        self._grid_size = 150
        self._grid_enabled = False  # Hide grid lines by default
        
        # Drawing mode
        self._drawing_mode = False
        self._temp_arrow = None
        
        # Arrow creation state
        self._arrow_creation_mode = False
        self._arrow_start_node = None
        self._current_arrow = None
        
        # Node naming counter (starts at 0 for 'A')
        self._node_counter = 0
        
        # Arrow naming counter (starts at 0 for 'a')
        self._arrow_counter = 0
        
        # Cycle detection
        self._cycle_detector = CycleDetector()
        self._highlighted_cycles = []  # Track currently highlighted cycles
        
        # Validation timer for touch screen safety (less frequent)
        self._validation_timer = QTimer()
        self._validation_timer.timeout.connect(self._validate_arrows_and_cycles)
        self._validation_timer.start(5000)  # Validate every 5 seconds
        
    def drawBackground(self, painter, rect):
        """Draw the grid background."""
        super().drawBackground(painter, rect)
        
        if not self._grid_enabled:
            return
            
        # Draw grid
        painter.setPen(QPen(QColor(200, 200, 200), 1))
        
        # Vertical lines
        left = int(rect.left()) - (int(rect.left()) % self._grid_size)
        top = int(rect.top()) - (int(rect.top()) % self._grid_size)
        
        lines = []
        x = left
        while x < rect.right():
            lines.append([int(x), int(rect.top()), int(x), int(rect.bottom())])
            x += self._grid_size
            
        y = top
        while y < rect.bottom():
            lines.append([int(rect.left()), int(y), int(rect.right()), int(y)])
            y += self._grid_size
            
        for line in lines:
            painter.drawLine(line[0], line[1], line[2], line[3])
    
    def addItem(self, item):
        """Override addItem to trigger cycle detection."""
        super().addItem(item)
        # Schedule cycle detection after item is added
        QTimer.singleShot(100, self._detect_and_highlight_cycles)
    
    def removeItem(self, item):
        """Override removeItem to trigger cycle detection."""
        super().removeItem(item)
        # Schedule cycle detection after item is removed
        QTimer.singleShot(100, self._detect_and_highlight_cycles)
    
    def snap_to_grid(self, point):
        """Snap a point to the nearest grid intersection."""
        # Find the nearest grid intersection
        grid_x = round(point.x() / self._grid_size) * self._grid_size
        grid_y = round(point.y() / self._grid_size) * self._grid_size
        
        from PyQt6.QtCore import QPointF
        return QPointF(grid_x, grid_y)
    
    def set_grid_enabled(self, enabled):
        """Enable or disable the grid."""
        self._grid_enabled = enabled
        self.update()
    
    def set_grid_size(self, size):
        """Set the grid size."""
        self._grid_size = size
        self.update()
    
    def mouseDoubleClickEvent(self, event):
        """Handle double-click events to add objects or create arrows."""
        # Find all items at the clicked position
        items_at_pos = self.items(event.scenePos())
        
        # Look for the first Object node (ignore arrows)
        target_object = None
        for item in items_at_pos:
            if hasattr(item, 'get_text'):  # This identifies Object nodes
                target_object = item
                break
        
        # If we clicked on an Object and not in arrow creation mode, start arrow creation
        if target_object and not self._arrow_creation_mode:
            self.start_arrow_creation(target_object)
            return
        
        # If we clicked on an Object and we're in arrow creation mode, finish the arrow
        if target_object and self._arrow_creation_mode:
            self.finish_arrow_creation(target_object)
            return
        
        # If we're in arrow creation mode and clicked empty space, create new object and connect
        if self._arrow_creation_mode:
            self.create_object_and_finish_arrow(event.scenePos())
            return
        
        # Otherwise, create a new object at the double-click position
        from object_node import Object
        
        pos = self.snap_to_grid(event.scenePos())
        
        # Check if position is occupied and find nearest free position if needed
        if self._is_grid_position_occupied(pos):
            pos = self._find_nearest_free_grid_position(pos)
        
        # Generate alphabetical name (A, B, C, ..., Z, A', B', C', etc.)
        node_name = self._get_next_node_name()
        
        # Create object at the snapped grid position
        obj = Object(node_name)
        
        # Create and push undo command instead of directly adding
        from undo_commands import PlaceObject
        from PyQt6.QtWidgets import QApplication
        
        command = PlaceObject(self, obj, pos)
        app = QApplication.instance()
        app.undo_stack.push(command)
        
        # Increment counter for next node
        self._node_counter += 1
        
        # Don't call super() to prevent default behavior
    
    def gather_object_names(self):
        """Return a set of all existing Object names in the scene."""
        from object_node import Object
        names = set()
        for item in self.items():
            if isinstance(item, Object):
                names.add(item.get_text())
        return names
    
    def next_available_object_name(self):
        """Find the next available object name in sequence A, B, ..., Z, A', B', ..."""
        existing_names = self.gather_object_names()
        
        apostrophe_count = 0
        while True:
            # Try each letter A-Z with current apostrophe count
            for letter_index in range(26):
                letter = chr(ord('A') + letter_index)
                apostrophes = "'" * apostrophe_count
                candidate_name = letter + apostrophes
                
                if candidate_name not in existing_names:
                    return candidate_name
            
            # If all letters with current apostrophe count are taken, add more apostrophes
            apostrophe_count += 1
    
    def gather_arrow_names(self):
        """Return a set of all existing Arrow names in the scene."""
        from arrow import Arrow
        names = set()
        for item in self.items():
            if isinstance(item, Arrow):
                names.add(item.get_text())
        return names
    
    def next_available_arrow_name(self):
        """Find the next available arrow name in sequence a, b, ..., z, a', b', ..."""
        existing_names = self.gather_arrow_names()
        
        apostrophe_count = 0
        while True:
            # Try each letter a-z with current apostrophe count
            for letter_index in range(26):
                letter = chr(ord('a') + letter_index)
                apostrophes = "'" * apostrophe_count
                candidate_name = letter + apostrophes
                
                if candidate_name not in existing_names:
                    return candidate_name
            
            # If all letters with current apostrophe count are taken, add more apostrophes
            apostrophe_count += 1
    
    def _get_next_node_name(self):
        """Generate the next alphabetical node name (A, B, C, ..., Z, A', B', C', etc.)."""
        # Use the new smart naming system
        return self.next_available_object_name()
    
    def _get_next_arrow_name(self):
        """Generate the next alphabetical arrow name (a, b, c, ..., z, a', b', c', etc.)."""
        # Use the new smart naming system
        return self.next_available_arrow_name()
    
    def mouseMoveEvent(self, event):
        """Handle mouse move events for arrow creation."""
        if self._arrow_creation_mode:
            self.update_arrow_end_point(event.scenePos())
        
        super().mouseMoveEvent(event)
    
    def mousePressEvent(self, event):
        """Handle mouse press events."""
        from PyQt6.QtCore import Qt
        
        # Validate arrows on any mouse press to catch orphaned arrows
        self._validate_arrows_and_cycles()
        
        # Check for right-click to cancel arrow creation
        if event.button() == Qt.MouseButton.RightButton and self._arrow_creation_mode:
            self.cancel_arrow_creation()
            return
        
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release events."""
        # Validate arrows on mouse release to catch orphaned arrows from touch interactions
        self._validate_arrows_and_cycles()
        super().mouseReleaseEvent(event)
    
    def keyPressEvent(self, event):
        """Handle key press events."""
        from PyQt6.QtCore import Qt
        
        # Check for ESC key to cancel arrow creation
        if event.key() == Qt.Key.Key_Escape and self._arrow_creation_mode:
            self.cancel_arrow_creation()
            return
        
        # Check for Delete key to delete selected items
        if event.key() == Qt.Key.Key_Delete:
            self.delete_selected_items()
            return
        
        super().keyPressEvent(event)
    
    def delete_selected_items(self):
        """Delete the currently selected items from the scene."""
        selected_items = self.selectedItems()
        
        if not selected_items:
            return  # Nothing to delete
        
        # Filter out items that shouldn't be deleted
        deletable_items = []
        for item in selected_items:
            # Include Objects, Arrows, and AdditionalLabels
            if (hasattr(item, 'get_text') or  # Objects and Arrows
                hasattr(item, 'toPlainText')):  # AdditionalLabels
                deletable_items.append(item)
        
        if not deletable_items:
            return  # Nothing deletable selected
        
        # Create and execute delete command
        from undo_commands import DeleteItems
        from PyQt6.QtWidgets import QApplication
        
        command = DeleteItems(self, deletable_items)
        app = QApplication.instance()
        app.undo_stack.push(command)
    
    def focusOutEvent(self, event):
        """Handle focus out events - validate arrows when losing focus."""
        self._validate_arrows_and_cycles()
        super().focusOutEvent(event)
    
    def focusInEvent(self, event):
        """Handle focus in events - validate arrows when gaining focus.""" 
        self._validate_arrows_and_cycles()
        super().focusInEvent(event)
    
    def contextMenuEvent(self, event):
        """Handle right-click context menu on empty space."""
        from PyQt6.QtWidgets import QMenu
        from PyQt6.QtGui import QAction
        
        # Check if we clicked on empty space (no items)
        items_at_pos = self.items(event.scenePos())
        if not items_at_pos:
            menu = QMenu()
            
            # Add "Add Label" action
            add_label_action = QAction("Add Label", menu)
            add_label_action.triggered.connect(lambda: self.add_label_at_position(event.scenePos()))
            menu.addAction(add_label_action)
            
            # Show the menu at the cursor position
            menu.exec(event.screenPos())
        else:
            # Let items handle their own context menus
            super().contextMenuEvent(event)
    
    def add_label_at_position(self, position):
        """Add a new AdditionalLabel at the specified position."""
        from additional_label import AdditionalLabel
        from undo_commands import PlaceLabel
        from PyQt6.QtWidgets import QApplication
        
        # Create new label
        label = AdditionalLabel("New Label")
        
        # Create and push undo command
        command = PlaceLabel(self, label, position)
        app = QApplication.instance()
        app.undo_stack.push(command)
        
        # Start editing immediately
        label.start_editing()
        
        # Update status
        if hasattr(self.parent(), 'status_bar'):
            self.parent().status_bar.showMessage("Label added. Double-click to edit, right-click for options.")
    
    def get_grid_size(self):
        """Get the current grid size."""
        return self._grid_size
    
    def reset_node_counter(self):
        """Reset the node naming counter to start from 'A' again."""
        self._node_counter = 0
    
    def reset_arrow_counter(self):
        """Reset the arrow naming counter to start from 'a' again."""
        self._arrow_counter = 0
    
    def clear(self):
        """Clear the scene and reset the node counter."""
        super().clear()
        self.reset_node_counter()
        self.reset_arrow_counter()
        self.cancel_arrow_creation()
    
    def start_arrow_creation(self, start_node):
        """Start creating an arrow from the given node."""
        from arrow import Arrow
        
        self._arrow_creation_mode = True
        self._arrow_start_node = start_node
        
        # Create a temporary arrow
        self._current_arrow = Arrow(start_node, None)
        
        # Set the start point to the center of the start node
        start_rect = start_node.boundingRect()
        start_center = start_node.pos() + QPointF(
            start_rect.width() / 2, start_rect.height() / 2
        )
        self._current_arrow.set_start_point(start_center)
        
        self.addItem(self._current_arrow)
        
        # Update status
        if hasattr(self.parent(), 'status_bar'):
            self.parent().status_bar.showMessage("Creating arrow... Double-click target node or empty space to create new node. Right-click/ESC to cancel.")
    
    def cancel_arrow_creation(self):
        """Cancel the current arrow creation."""
        if self._arrow_creation_mode and self._current_arrow:
            self.removeItem(self._current_arrow)
            
        self._arrow_creation_mode = False
        self._arrow_start_node = None
        self._current_arrow = None
        
        # Validate all arrows and remove incomplete ones
        self._validate_arrows_and_cycles()
        
        # Update status
        if hasattr(self.parent(), 'status_bar'):
            self.parent().status_bar.showMessage("Arrow creation cancelled. Double-click canvas to add objects. Right-click objects to edit names.")
    
    def _validate_arrows_and_cycles(self):
        """Remove any arrows that don't have both source and target nodes and detect cycles."""
        from arrow import Arrow
        from object_node import Object
        
        # First, validate arrows as before
        arrows_to_remove = []
        for item in self.items():
            if isinstance(item, Arrow):
                # Check if arrow has both source and target
                source = item.get_source()
                target = item.get_target()
                
                if source is None or target is None:
                    # Only add to removal list if the item is actually in this scene
                    if item.scene() == self:
                        arrows_to_remove.append(item)
        
        # Remove incomplete arrows
        for arrow in arrows_to_remove:
            try:
                self.removeItem(arrow)
            except:
                # Silently ignore errors if item is already removed or not in scene
                pass
        
        # Update status if arrows were removed
        if arrows_to_remove and hasattr(self.parent(), 'status_bar'):
            self.parent().status_bar.showMessage(f"Removed {len(arrows_to_remove)} incomplete arrow(s).")
        
        # Now detect and highlight cycles
        self._detect_and_highlight_cycles()
    
    def _detect_and_highlight_cycles(self):
        """Detect cycles in the graph and highlight them in red."""
        from arrow import Arrow
        from object_node import Object
        
        # Clear previous highlighting
        self._clear_cycle_highlighting()
        
        # Get all nodes and arrows
        nodes = []
        arrows = []
        for item in self.items():
            if isinstance(item, Object):
                nodes.append(item)
            elif isinstance(item, Arrow):
                arrows.append(item)
        
        # Find cycles
        cycles = self._cycle_detector.find_cycles(nodes, arrows)
        
        # Highlight each cycle
        for cycle in cycles:
            if len(cycle) > 1:  # Valid cycle
                self._highlight_cycle(cycle, arrows)
        
        # Store cycles for cleanup
        self._highlighted_cycles = cycles
        
        # Update status if cycles found
        if cycles and hasattr(self.parent(), 'status_bar'):
            self.parent().status_bar.showMessage(f"Warning: {len(cycles)} cycle(s) detected! Remove nodes or arrows to break cycles.")
    
    def _highlight_cycle(self, cycle_nodes, arrows):
        """Highlight a specific cycle in red."""
        from arrow import Arrow
        
        # Get the arrows that form the cycle
        cycle_arrows = self._cycle_detector.get_cycle_arrows(cycle_nodes, arrows)
        
        # Highlight nodes in the cycle (excluding the duplicate end node)
        unique_nodes = cycle_nodes[:-1] if len(cycle_nodes) > 1 else cycle_nodes
        for node in unique_nodes:
            if hasattr(node, 'set_highlight_color'):
                node.set_highlight_color(QColor(255, 0, 0, 100))  # Red with transparency
        
        # Highlight arrows in the cycle
        for arrow in cycle_arrows:
            if hasattr(arrow, 'set_highlight_color'):
                arrow.set_highlight_color(QColor(255, 0, 0))  # Solid red
    
    def _clear_cycle_highlighting(self):
        """Clear all cycle highlighting."""
        from arrow import Arrow
        from object_node import Object
        
        # Clear highlighting from all items
        for item in self.items():
            if isinstance(item, (Object, Arrow)):
                if hasattr(item, 'clear_highlight_color'):
                    item.clear_highlight_color()
        
        self._highlighted_cycles = []
    
    def _is_grid_position_occupied(self, position):
        """Check if a grid position is already occupied by another object."""
        from object_node import Object
        
        # Snap position to grid intersection
        grid_x = round(position.x() / self._grid_size) * self._grid_size
        grid_y = round(position.y() / self._grid_size) * self._grid_size
        
        # Check all objects in the scene
        for item in self.items():
            if isinstance(item, Object):
                item_pos = item.pos()
                # Calculate the grid position for existing items
                item_grid_x = round(item_pos.x() / self._grid_size) * self._grid_size
                item_grid_y = round(item_pos.y() / self._grid_size) * self._grid_size
                
                if item_grid_x == grid_x and item_grid_y == grid_y:
                    return True
        return False
    
    def _find_nearest_free_grid_position(self, position):
        """Find the nearest free grid position to the given position."""
        from PyQt6.QtCore import QPointF
        
        grid_size = self._grid_size  # Use the scene's grid size
        
        # Find the nearest grid intersection
        grid_x = round(position.x() / grid_size) * grid_size
        grid_y = round(position.y() / grid_size) * grid_size
        
        # Use grid intersection position directly
        start_pos = QPointF(grid_x, grid_y)
        
        # If the original position is free, use it
        if not self._is_grid_position_occupied(start_pos):
            return start_pos
        
        # Search in expanding squares around the original position
        for radius in range(1, 20):  # Search up to 20 grid units away
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    # Only check positions on the edge of the current square
                    if abs(dx) == radius or abs(dy) == radius:
                        test_x = grid_x + dx * grid_size
                        test_y = grid_y + dy * grid_size
                        test_pos = QPointF(test_x, test_y)
                        
                        if not self._is_grid_position_occupied(test_pos):
                            return test_pos
        
        # Fallback: return original position if no free spot found
        return start_pos
    
    def finish_arrow_creation(self, end_node):
        """Finish creating the arrow by connecting to the end node."""
        if self._arrow_creation_mode and self._current_arrow:
            # Check if this would create a self-loop and prevent it
            if end_node == self._arrow_start_node:
                # Cancel the arrow creation for self-loops
                self.cancel_arrow_creation()
                # Show message to user
                if hasattr(self.parent(), 'status_bar'):
                    self.parent().status_bar.showMessage("Self-loops are not allowed.")
                return
            
            # Remove the temporary arrow
            self.removeItem(self._current_arrow)
            
            # Set the arrow name
            arrow_name = self._get_next_arrow_name()
            self._current_arrow.set_text(arrow_name)
            
            # Create and push undo command for arrow placement
            from undo_commands import PlaceArrow
            from PyQt6.QtWidgets import QApplication
            
            command = PlaceArrow(self, self._current_arrow, self._arrow_start_node, end_node)
            app = QApplication.instance()
            app.undo_stack.push(command)
            
            # Increment arrow counter for next arrow
            self._arrow_counter += 1
            
            # Reset state
            self._arrow_creation_mode = False
            self._arrow_start_node = None
            self._current_arrow = None
            
            # Validate all arrows and remove incomplete ones
            self._validate_arrows_and_cycles()
            
            # Update status
            if hasattr(self.parent(), 'status_bar'):
                self.parent().status_bar.showMessage("Arrow created. Double-click canvas to add objects. Right-click objects to edit names.")
        else:
            # Cancel if no valid arrow creation state
            self.cancel_arrow_creation()
    
    def create_object_and_finish_arrow(self, click_position):
        """Create a new object at the click position and finish the arrow to it."""
        if not self._arrow_creation_mode or not self._current_arrow:
            return
        
        # Remove the temporary arrow
        self.removeItem(self._current_arrow)
        
        # Snap position to grid and find nearest free position
        snapped_pos = self.snap_to_grid(click_position)
        free_pos = self._find_nearest_free_grid_position(snapped_pos)
        
        # Generate alphabetical name for the new object
        node_name = self._get_next_node_name()
        
        # Create the new object
        from object_node import Object
        new_obj = Object(node_name)
        
        # Set the arrow name
        arrow_name = self._get_next_arrow_name()
        self._current_arrow.set_text(arrow_name)
        
        # Create undo commands for both object and arrow placement
        from undo_commands import PlaceObject, PlaceArrow
        from PyQt6.QtWidgets import QApplication
        
        app = QApplication.instance()
        
        # Instead of using macro commands with setParent, execute both operations
        # and let each have their own undo command
        
        # First, place the object at the free grid position
        place_object_cmd = PlaceObject(self, new_obj, free_pos)
        app.undo_stack.push(place_object_cmd)
        
        # Then, place the arrow
        place_arrow_cmd = PlaceArrow(self, self._current_arrow, self._arrow_start_node, new_obj)
        app.undo_stack.push(place_arrow_cmd)
        
        # Increment counters for next items
        self._node_counter += 1
        self._arrow_counter += 1
        
        # Reset arrow creation state
        self._arrow_creation_mode = False
        self._arrow_start_node = None
        self._current_arrow = None
        
        # Validate all arrows and remove incomplete ones
        self._validate_arrows_and_cycles()
        
        # Update status
        if hasattr(self.parent(), 'status_bar'):
            self.parent().status_bar.showMessage(f"Created object '{node_name}' and connected with arrow '{arrow_name}'.")
    
    def update_arrow_end_point(self, point):
        """Update the end point of the arrow being created."""
        if self._arrow_creation_mode and self._current_arrow:
            # Calculate proper start point at edge of start node
            start_rect = self._arrow_start_node.boundingRect()
            start_center = self._arrow_start_node.pos() + QPointF(
                start_rect.width() / 2, start_rect.height() / 2
            )
            
            # Calculate direction from start center to mouse point
            dx = point.x() - start_center.x()
            dy = point.y() - start_center.y()
            
            # Calculate intersection with start node's boundary
            import math
            if abs(dx) > 0.001 or abs(dy) > 0.001:
                length = math.sqrt(dx * dx + dy * dy)
                dx_norm = dx / length
                dy_norm = dy / length
                
                # Get half dimensions
                half_width = start_rect.width() / 2
                half_height = start_rect.height() / 2
                
                # Calculate intersection point on the rectangle boundary
                if abs(dx_norm) > abs(dy_norm):
                    # Intersects with left or right edge
                    t = half_width / abs(dx_norm)
                else:
                    # Intersects with top or bottom edge
                    t = half_height / abs(dy_norm)
                
                # Calculate start point at edge
                start_edge = QPointF(
                    start_center.x() + dx_norm * t,
                    start_center.y() + dy_norm * t
                )
                self._current_arrow.set_start_point(start_edge)
            
            self._current_arrow.set_end_point(point)
