"""
Custom QGraphicsView for DAG diagrams.
"""
from PyQt6.QtWidgets import QGraphicsView
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QWheelEvent
from .proof_step_overlay import ProofStepOverlay


class DiagramView(QGraphicsView):
    """Custom graphics view for DAG diagrams with zoom and pan capabilities."""
    
    def __init__(self, scene=None, parent=None):
        super().__init__(scene, parent)
        
        # Start with NoDrag mode to allow item movement by default
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        
        # Enable anti-aliasing
        from PyQt6.QtGui import QPainter
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Zoom settings
        self._zoom_factor = 1.15
        self._min_zoom = 0.1
        self._max_zoom = 5.0
        self._current_zoom = 1.0
        
        # Enable mouse tracking and focus for key events
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        # Create proof step overlay
        self.proof_step_overlay = ProofStepOverlay(self, self)
        
        # Connect to scene selection changes
        if scene:
            self.setScene(scene)
            scene.selectionChanged.connect(self.on_selection_changed)
        
        # Set transformation anchor to mouse position for zoom
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        
        # Double-click detection
        self._suppress_overlay_timer = None
        self._suppress_overlay = False
        
        # Proof buttons control - default disabled
        self._proof_buttons_enabled = False
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        
        # Press and hold timer for context menu
        from PyQt6.QtCore import QTimer
        self._press_hold_timer = QTimer()
        self._press_hold_timer.setSingleShot(True)
        self._press_hold_timer.timeout.connect(self._show_context_menu)
        self._press_hold_duration = 500  # milliseconds
        self._press_hold_pos = None
        
    def wheelEvent(self, event: QWheelEvent):
        """Handle mouse wheel events for zooming."""
        # Get the angle delta
        angle_delta = event.angleDelta().y()
        
        if angle_delta > 0:
            # Zoom in
            if self._current_zoom < self._max_zoom:
                self.scale(self._zoom_factor, self._zoom_factor)
                self._current_zoom *= self._zoom_factor
        else:
            # Zoom out
            if self._current_zoom > self._min_zoom:
                self.scale(1 / self._zoom_factor, 1 / self._zoom_factor)
                self._current_zoom /= self._zoom_factor
    
    def mousePressEvent(self, event):
        """Handle mouse press events."""
        # Stop any existing press-hold timer
        self._press_hold_timer.stop()
        
        # Check if the click is on the proof step overlay area
        if hasattr(self, 'proof_step_overlay') and self.proof_step_overlay.isVisible():
            overlay_rect = self.proof_step_overlay.geometry()
            if overlay_rect.contains(event.pos()):
                # Let the overlay handle the mouse event - don't interfere
                super().mousePressEvent(event)
                return
        
        # Check if we clicked on an item first
        item = self.itemAt(event.pos())
        
        if event.button() == Qt.MouseButton.LeftButton and item and hasattr(item, 'get_text'):
            # Left click on an object node - prepare for potential drag
            self._potential_drag_item = item
            self._drag_start_pos = event.pos()
            self._drag_start_scene_pos = self.mapToScene(event.pos())
            self._drag_start_item_pos = item.pos()
            self._is_actually_dragging = False
            self._drag_threshold = 5  # pixels
            # Allow normal selection to proceed first
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
        elif event.button() == Qt.MouseButton.LeftButton and not item:
            # Left click on empty space - prepare for panning or context menu
            self._canvas_drag_start = event.pos()
            self._is_canvas_dragging = False
            self._canvas_drag_threshold = 5  # pixels
            
            # Start press-hold timer for context menu
            self._press_hold_pos = event.pos()
            self._press_hold_timer.start(self._press_hold_duration)
            
            # Don't set drag mode yet - wait to see if it's a drag or hold
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
        else:
            # Clear potential drag
            self._potential_drag_item = None
            
            if event.button() == Qt.MouseButton.MiddleButton:
                # Enable pan mode with middle mouse button
                self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
            elif event.button() == Qt.MouseButton.RightButton:
                # Handle right-click context menus
                if item:
                    # Right-click on item - let item handle its context menu
                    super().mousePressEvent(event)
                    return
        
        # Always call super to allow normal selection/interaction
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Handle mouse move events."""
        # Stop press-hold timer if mouse moves (it's a drag, not a hold)
        self._press_hold_timer.stop()
        
        # Check if we have a potential canvas drag that hasn't started yet
        if (hasattr(self, '_canvas_drag_start') and self._canvas_drag_start and 
            not hasattr(self, '_is_canvas_dragging')):
            self._is_canvas_dragging = False
        
        # Check if we should start canvas panning
        if (hasattr(self, '_canvas_drag_start') and self._canvas_drag_start and 
            not self._is_canvas_dragging):
            
            move_distance = (event.pos() - self._canvas_drag_start).manhattanLength()
            if move_distance > self._canvas_drag_threshold:
                self._is_canvas_dragging = True
                # Enable scroll hand drag for panning
                self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
                # Need to simulate a mouse press to start the drag
                from PyQt6.QtGui import QMouseEvent
                from PyQt6.QtCore import QPointF
                press_event = QMouseEvent(
                    QMouseEvent.Type.MouseButtonPress,
                    QPointF(self._canvas_drag_start),
                    Qt.MouseButton.LeftButton,
                    Qt.MouseButton.LeftButton,
                    Qt.KeyboardModifier.NoModifier
                )
                super().mousePressEvent(press_event)
        
        # Check if we have a potential item drag that hasn't started yet
        if (hasattr(self, '_potential_drag_item') and self._potential_drag_item and 
            not self._is_actually_dragging):
            
            # Check if we've moved far enough to start dragging
            move_distance = (event.pos() - self._drag_start_pos).manhattanLength()
            if move_distance > self._drag_threshold:
                self._is_actually_dragging = True
        
        # Check if we're actually dragging an item
        if (hasattr(self, '_potential_drag_item') and self._potential_drag_item and 
            self._is_actually_dragging):
            # Calculate the movement delta
            current_scene_pos = self.mapToScene(event.pos())
            scene_delta = current_scene_pos - self._drag_start_scene_pos
            
            # Move the item by the delta
            new_pos = self._drag_start_item_pos + scene_delta
            self._potential_drag_item.setPos(new_pos)
            return
        
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release events."""
        # Stop press-hold timer
        self._press_hold_timer.stop()
        
        # Check if we were dragging the canvas
        if (hasattr(self, '_is_canvas_dragging') and self._is_canvas_dragging and 
            event.button() == Qt.MouseButton.LeftButton):
            # Reset canvas drag state
            self._canvas_drag_start = None
            self._is_canvas_dragging = False
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
            super().mouseReleaseEvent(event)
            return
        
        # Check if we were dragging an item
        if (hasattr(self, '_potential_drag_item') and self._potential_drag_item and 
            event.button() == Qt.MouseButton.LeftButton):
            
            if self._is_actually_dragging:
                # Create undo command for the move
                if hasattr(self._potential_drag_item, 'get_text'):
                    end_position = self._potential_drag_item.pos()
                    if self._drag_start_item_pos != end_position:
                        from core.undo_commands import MoveObject
                        from PyQt6.QtWidgets import QApplication
                        
                        command = MoveObject(self._potential_drag_item, self._drag_start_item_pos, end_position)
                        app = QApplication.instance()
                        app.undo_stack.push(command)
            
            # Clear dragging state
            self._potential_drag_item = None
            self._is_actually_dragging = False
            super().mouseReleaseEvent(event)
            return
        
        # Clear canvas drag state if it was just a click
        if hasattr(self, '_canvas_drag_start'):
            self._canvas_drag_start = None
            self._is_canvas_dragging = False
        
        if event.button() == Qt.MouseButton.MiddleButton:
            # Return to normal drag mode after middle mouse release
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
            print("Reset drag mode to NoDrag")
        elif event.button() == Qt.MouseButton.LeftButton:
            # Reset to NoDrag after left button release
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
            print("Reset drag mode to NoDrag")
        
        super().mouseReleaseEvent(event)
    
    def _show_context_menu(self):
        """Show context menu for empty canvas after press-and-hold."""
        if not self._press_hold_pos:
            return
        
        from PyQt6.QtWidgets import QMenu
        menu = QMenu(self)
        
        # Add Object action
        add_object_action = menu.addAction("Add Object")
        add_object_action.triggered.connect(lambda: self._add_object_at_pos(self._press_hold_pos))
        
        # Show menu at the press position
        global_pos = self.mapToGlobal(self._press_hold_pos)
        menu.exec(global_pos)
        
        # Clear press hold state
        self._press_hold_pos = None
    
    def _add_object_at_pos(self, pos):
        """Add a new object at the specified position."""
        scene = self.scene()
        if not scene:
            return
        
        # Convert view position to scene position
        scene_pos = self.mapToScene(pos)
        
        # Create new object
        from widget.object_node import Object
        new_object = Object("Object")
        new_object.setPos(scene_pos)
        
        # Add to scene via undo command
        from core.undo_commands import PlaceObject
        from PyQt6.QtWidgets import QApplication
        
        command = PlaceObject(scene, new_object, scene_pos)
        app = QApplication.instance()
        app.undo_stack.push(command)
    
    def keyPressEvent(self, event):
        """Handle key press events."""
        if event.key() == Qt.Key.Key_Plus or event.key() == Qt.Key.Key_Equal:
            # Zoom in with + key
            if self._current_zoom < self._max_zoom:
                self.scale(self._zoom_factor, self._zoom_factor)
                self._current_zoom *= self._zoom_factor
        elif event.key() == Qt.Key.Key_Minus:
            # Zoom out with - key
            if self._current_zoom > self._min_zoom:
                self.scale(1 / self._zoom_factor, 1 / self._zoom_factor)
                self._current_zoom /= self._zoom_factor
        elif event.key() == Qt.Key.Key_0:
            # Reset zoom with 0 key
            self.reset_zoom()
        else:
            super().keyPressEvent(event)
    
    def mouseDoubleClickEvent(self, event):
        """Handle mouse double-click events."""
        # Suppress overlay for a short time after double-click
        self._suppress_overlay = True
        
        # Set up timer to clear suppression after 100ms
        from PyQt6.QtCore import QTimer
        if self._suppress_overlay_timer:
            self._suppress_overlay_timer.stop()
        
        self._suppress_overlay_timer = QTimer()
        self._suppress_overlay_timer.timeout.connect(self._clear_overlay_suppression)
        self._suppress_overlay_timer.setSingleShot(True)
        self._suppress_overlay_timer.start(100)  # 100ms delay
        
        super().mouseDoubleClickEvent(event)
    
    def _clear_overlay_suppression(self):
        """Clear the overlay suppression flag."""
        self._suppress_overlay = False
        if self._suppress_overlay_timer:
            self._suppress_overlay_timer.stop()
            self._suppress_overlay_timer = None
    
    def reset_zoom(self):
        """Reset zoom to 100%."""
        self.resetTransform()
        self._current_zoom = 1.0
    
    def fit_in_view_all(self):
        """Fit all items in the view."""
        if self.scene():
            items_rect = self.scene().itemsBoundingRect()
            if not items_rect.isEmpty():
                self.fitInView(items_rect, Qt.AspectRatioMode.KeepAspectRatio)
                # Update zoom level based on current transform
                transform = self.transform()
                self._current_zoom = transform.m11()  # Get scale factor
    
    def get_zoom_level(self):
        """Get the current zoom level."""
        return self._current_zoom
    
    def set_zoom_level(self, zoom):
        """Set the zoom level."""
        if self._min_zoom <= zoom <= self._max_zoom:
            # Reset transform and apply new zoom
            self.resetTransform()
            self.scale(zoom, zoom)
            self._current_zoom = zoom
    
    def resizeEvent(self, event):
        """Handle resize events to update overlay size."""
        super().resizeEvent(event)
        if hasattr(self, 'proof_step_overlay'):
            self.proof_step_overlay.resize(self.size())
    
    def set_proof_buttons_enabled(self, enabled):
        """Enable or disable proof step buttons overlay."""
        self._proof_buttons_enabled = enabled
        
        if not enabled:
            # Hide overlay if disabled
            if hasattr(self, 'proof_step_overlay'):
                self.proof_step_overlay.hide()
        else:
            # Re-trigger selection changed to show overlay if appropriate
            self.on_selection_changed()
    
    def on_selection_changed(self):
        """Handle selection changes in the scene."""
        # Don't show overlay if we just had a double-click
        if hasattr(self, '_suppress_overlay') and self._suppress_overlay:
            return
        
        # Don't show overlay if proof buttons are disabled
        if not getattr(self, '_proof_buttons_enabled', False):
            return
            
        if not hasattr(self, 'proof_step_overlay'):
            return
        
        scene = self.scene()
        if not scene:
            return
        
        selected_items = scene.selectedItems()
        
        # Separate objects and arrows
        selected_objects = []
        selected_arrows = []
        
        for item in selected_items:
            # Check if it's an object (has get_text and is not an arrow)
            if hasattr(item, 'get_text'):
                if hasattr(item, 'get_source'):  # It's an arrow
                    selected_arrows.append(item)
                else:  # It's an object
                    selected_objects.append(item)
        
        # Update overlay
        self.proof_step_overlay.update_for_selection(selected_objects, selected_arrows)
    
    def setScene(self, scene):
        """Override setScene to connect selection signals."""
        super().setScene(scene)
        if scene:
            scene.selectionChanged.connect(self.on_selection_changed)
