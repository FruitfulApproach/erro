"""
Additional label for DAG diagrams - movable text items.
"""
from PyQt6.QtWidgets import QGraphicsTextItem, QGraphicsItem, QMenu
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor, QAction


class AdditionalLabel(QGraphicsTextItem):
    """Additional text label that can be moved around the diagram."""
    
    def __init__(self, text="Label", parent=None):
        super().__init__(text, parent)
        
        # Make the label movable and selectable
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        
        # Set default font and styling
        font = QFont("Arial", 12)
        self.setFont(font)
        self.setDefaultTextColor(QColor(0, 0, 0))
        
        # Set higher Z-value to appear on top
        self.setZValue(2)
        
        # Enable text editing
        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextEditorInteraction)
        
    def contextMenuEvent(self, event):
        """Handle right-click context menu."""
        menu = QMenu()
        
        # Add "Edit Text" action
        edit_text_action = QAction("Edit Text", menu)
        edit_text_action.triggered.connect(self.start_editing)
        menu.addAction(edit_text_action)
        
        # Add "Delete" action
        delete_action = QAction("Delete", menu)
        delete_action.triggered.connect(self.delete_label)
        menu.addAction(delete_action)
        
        # Show the menu at the cursor position
        menu.exec(event.screenPos())
    
    def start_editing(self):
        """Start editing the text."""
        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextEditorInteraction)
        self.setFocus()
    
    def delete_label(self):
        """Delete this label from the scene."""
        from core.undo_commands import DeleteLabel
        from PyQt6.QtWidgets import QApplication
        
        if self.scene():
            # Create and push undo command
            command = DeleteLabel(self.scene(), self)
            app = QApplication.instance()
            app.undo_stack.push(command)
    
    def itemChange(self, change, value):
        """Handle item changes, particularly position changes for grid snapping."""
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            # Optional: Snap to grid (can be enabled/disabled)
            # For now, we'll allow free positioning
            return value
        
        return super().itemChange(change, value)
    
    def focusOutEvent(self, event):
        """Handle when the item loses focus (finish editing)."""
        # Disable text editing when focus is lost
        self.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        super().focusOutEvent(event)
    
    def mouseDoubleClickEvent(self, event):
        """Handle double-click to start editing."""
        self.start_editing()
        super().mouseDoubleClickEvent(event)
    
    def type(self):
        """Return the type identifier for this item."""
        return QGraphicsItem.UserType + 3
