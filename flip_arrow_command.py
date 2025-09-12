"""
FlipArrowCommand for the Pythom DAG diagram editor.
"""
from PyQt6.QtGui import QUndoCommand


class FlipArrowCommand(QUndoCommand):
    """Command to flip the direction of an arrow by swapping source and target."""
    
    def __init__(self, arrow):
        super().__init__(f"Flip Arrow '{arrow.get_text()}'")
        self.arrow = arrow
        self.original_source = arrow.get_source()
        self.original_target = arrow.get_target()
    
    def redo(self):
        """Execute the flip."""
        # Swap the source and target nodes
        self.arrow.set_nodes(self.original_target, self.original_source)
    
    def undo(self):
        """Undo the flip."""
        # Restore the original source and target
        self.arrow.set_nodes(self.original_source, self.original_target)
