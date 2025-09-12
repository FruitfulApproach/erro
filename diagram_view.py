"""
Custom QGraphicsView for DAG diagrams.
"""
from PyQt6.QtWidgets import QGraphicsView
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QWheelEvent


class DiagramView(QGraphicsView):
    """Custom graphics view for DAG diagrams with zoom and pan capabilities."""
    
    def __init__(self, scene=None, parent=None):
        super().__init__(scene, parent)
        
        # Enable drag mode for panning
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        
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
        
        # Set transformation anchor to mouse position for zoom
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        
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
        if event.button() == Qt.MouseButton.MiddleButton:
            # Enable pan mode with middle mouse button
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        else:
            self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release events."""
        if event.button() == Qt.MouseButton.MiddleButton:
            # Return to normal drag mode
            self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        
        super().mouseReleaseEvent(event)
    
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
