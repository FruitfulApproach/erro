"""
Object node for DAG diagrams - represents data or process nodes.
"""
from PyQt6.QtWidgets import QGraphicsItem, QMenu
from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QAction
from node import Node


class Object(Node):
    """Object node representing a data or process element in the DAG."""
    
    def __init__(self, text="Object", parent=None):
        super().__init__(parent)
        self._text = text
        self._font = QFont("Arial", 12, QFont.Weight.Bold)  # Bold font for better visibility
        
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
        self._text = text
        self.prepareGeometryChange()  # Notify that geometry will change
        self.update()
    
    def get_text(self):
        """Get the text displayed on the object."""
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
        
        # Add "Delete" action
        delete_action = QAction("Delete", menu)
        delete_action.triggered.connect(self.delete_object)
        menu.addAction(delete_action)
        
        # Show the menu at the cursor position
        menu.exec(event.screenPos())
    
    def edit_name(self):
        """Open the rename dialog to edit the object's name."""
        from object_rename_dialog import ObjectRenameDialog
        from undo_commands import RenameObject
        from PyQt6.QtWidgets import QApplication
        
        dialog = ObjectRenameDialog(self._text, self.scene().views()[0])
        if dialog.exec() == dialog.DialogCode.Accepted:
            new_name = dialog.get_name()
            if new_name and new_name != self._text:  # Only update if name changed
                # Create and push undo command
                command = RenameObject(self, self._text, new_name)
                app = QApplication.instance()
                app.undo_stack.push(command)
    
    def delete_object(self):
        """Delete this object."""
        from undo_commands import DeleteItems
        from PyQt6.QtWidgets import QApplication
        
        command = DeleteItems(self.scene(), [self])
        app = QApplication.instance()
        app.undo_stack.push(command)
