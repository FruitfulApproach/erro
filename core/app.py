"""
Custom QApplication subclass for the Pythom DAG diagram editor.
"""
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QUndoStack


class PythomApp(QApplication):
    """Custom application class with undo/redo support."""
    
    def __init__(self, argv):
        super().__init__(argv)
        
        # Initialize the undo stack
        self.undo_stack = QUndoStack(self)
        
        # Set application properties
        self.setApplicationName("Pythom")
        self.setApplicationVersion("1.0")
        self.setOrganizationName("Pythom")
    
    def get_undo_stack(self):
        """Get the global undo stack."""
        return self.undo_stack
