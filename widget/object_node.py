"""
Object node for DAG diagrams - represents data or process nodes.
"""
from PyQt6.QtWidgets import QGraphicsItem, QMenu
from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QAction
from .node import Node


class Object(Node):
    """Object node representing a data or process element in the DAG."""
    
    def __init__(self, text="Object", parent=None):
        super().__init__(parent)
        self._text = text
        self._base_name = text  # Store the original/base name
        self._font = QFont("Arial", 14, QFont.Weight.Bold)  # Bold font for better visibility
        self._label_manually_hidden = False  # Manual label hiding flag
        
        # Object-specific styling - transparent background and border
        self.set_size(80, 80)  # Square 80x80 pixels, fits well in 100x100 grid
        self._pen = QPen(QColor(0, 0, 0, 0), 0)  # Transparent border
        self._brush = QBrush(QColor(0, 0, 0, 0))  # Transparent background
        
        # Store original transparent values for highlight restore
        self._original_pen = self._pen
        self._original_brush = self._brush
        
        # For rounded rectangle
        self._corner_radius = 10
        
        # Set object to appear on top of arrows
        self.setZValue(1)
    
    def boundingRect(self):
        """Return the bounding rectangle of the node based on text content."""
        from PyQt6.QtGui import QFontMetrics
        from PyQt6.QtCore import QRectF
        
        # Calculate text dimensions using font metrics
        font_metrics = QFontMetrics(self._font)
        text_rect = font_metrics.boundingRect(self._text)
        
        # Add double padding (2 * pad_size as specified)
        pad_size = 10  # Double the previous padding (was 5)
        w = text_rect.width() + 2 * pad_size
        h = text_rect.height() + 2 * pad_size
        
        # If width is less than height, make the object square using height
        if w < h:
            w = h
        
        # Return rectangle centered around origin
        return QRectF(-w/2, -h/2, w, h)
        
    def paint(self, painter, option, widget=None):
        """Paint the object node."""
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Get the bounding rectangle (now centered around origin)
        rect = self.boundingRect()
        
        # Draw rounded rectangle
        painter.setPen(self._pen)
        painter.setBrush(self._brush)
        painter.drawRoundedRect(rect, self._corner_radius, self._corner_radius)
        
        # Draw text centered in a smaller rectangle with padding
        if not self._label_manually_hidden:
            padding = 10  # Double the previous padding (was 5)
            text_rect = rect.adjusted(padding, padding, -padding, -padding)
            painter.setPen(QPen(QColor(0, 0, 0)))
            painter.setFont(self._font)
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, self._text)
        
        # Draw selection highlight if selected
        if self.isSelected():
            painter.setPen(QPen(QColor(255, 165, 0), 3))  # Orange selection
            painter.setBrush(QBrush())  # No fill
            painter.drawRoundedRect(rect, self._corner_radius, self._corner_radius)
    
    def set_text(self, text):
        """Set the text displayed on the object."""
        old_text = self._text
        self._text = text
        self.prepareGeometryChange()  # Notify that geometry will change
        self.update()
        
        # Emit signal if text actually changed
        if old_text != text:
            self.name_changed.emit(self._base_name)  # Emit base name, not display text
    
    def set_base_name(self, name):
        """Set the base name of the object."""
        old_name = self._base_name
        self._base_name = name
        # If no element prefix, also update display text
        if ':' not in self._text:
            self.set_text(name)
        else:
            # Update display text while preserving element prefix
            parts = self._text.split(':', 1)
            if len(parts) == 2:
                element = parts[0]
                new_display = f"{element}:{name}"
                self.set_text(new_display)
        
        # Emit signal if base name actually changed
        if old_name != name:
            self.name_changed.emit(name)
    
    def get_text(self):
        """Get the base name of the object (not the display text)."""
        return self._base_name
    
    def get_display_text(self):
        """Get the text displayed visually on the object."""
        return self._text
    
    def type(self):
        """Return the type identifier for this item."""
        return QGraphicsItem.UserType + 1
    
    def contextMenuEvent(self, event):
        """Handle right-click context menu."""
        menu = QMenu()
        
        # Add "Edit Name" action
        edit_name_action = QAction("Edit Name", menu)
        edit_name_action.triggered.connect(self.edit_name)
        menu.addAction(edit_name_action)
        
        # Add separator
        menu.addSeparator()
        
        # Add "Hide Label" toggle action
        hide_label_action = QAction("Hide Label", menu)
        hide_label_action.setCheckable(True)
        hide_label_action.setChecked(self._label_manually_hidden)
        hide_label_action.triggered.connect(self.toggle_label_visibility)
        menu.addAction(hide_label_action)
        
        # Add separator
        menu.addSeparator()
        
        # Add "Delete" action
        delete_action = QAction("Delete", menu)
        delete_action.triggered.connect(self.delete_object)
        menu.addAction(delete_action)
        
        # Show the menu at the cursor position
        menu.exec(event.screenPos())
    
    def edit_name(self):
        """Open the rename dialog to edit the object's name."""
        from dialog.object_rename_dialog import ObjectRenameDialog
        from core.undo_commands import RenameObject
        from PyQt6.QtWidgets import QApplication
        
        dialog = ObjectRenameDialog(self._base_name, self.scene().views()[0])
        if dialog.exec() == dialog.DialogCode.Accepted:
            new_name = dialog.get_name()
            if new_name and new_name != self._base_name:  # Compare with base name
                # Create and push undo command
                command = RenameObject(self, self._base_name, new_name)
                app = QApplication.instance()
                app.undo_stack.push(command)
    
    def delete_object(self):
        """Delete this object."""
        from core.undo_commands import DeleteItems
        from PyQt6.QtWidgets import QApplication
        
        command = DeleteItems(self.scene(), [self])
        app = QApplication.instance()
        app.undo_stack.push(command)
    
    def toggle_label_visibility(self):
        """Toggle manual label visibility."""
        self._label_manually_hidden = not self._label_manually_hidden
        self.update()  # Trigger repaint
