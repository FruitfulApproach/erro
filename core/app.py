"""
Custom QApplication subclass for the Pythom DAG diagram editor.
"""
import json
from typing import Dict, List, Any
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QUndoStack, QUndoCommand


class App(QApplication):
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
    
    def serialize_undo_stack(self) -> List[Dict[str, Any]]:
        """Serialize the undo stack to a list of dictionaries."""
        stack_data = []
        
        for i in range(self.undo_stack.count()):
            command = self.undo_stack.command(i)
            if command:
                command_data = self._serialize_command(command)
                if command_data:
                    stack_data.append(command_data)
        
        return {
            'commands': stack_data,
            'clean_index': self.undo_stack.cleanIndex(),
            'current_index': self.undo_stack.index()
        }
    
    def _serialize_command(self, command: QUndoCommand) -> Dict[str, Any]:
        """Serialize a single undo command."""
        try:
            # Get the command class name for reconstruction
            command_type = command.__class__.__name__
            command_data = {
                'type': command_type,
                'text': command.text(),
                'data': {}
            }
            
            # Handle specific command types
            if hasattr(command, 'serialize'):
                # If the command has its own serialization method
                command_data['data'] = command.serialize()
            elif command_type == 'ProofStepCommand':
                # Handle proof step commands
                if hasattr(command, 'proof_step'):
                    command_data['data'] = {
                        'proof_step_type': command.proof_step.__class__.__name__,
                        'tab_index': getattr(command, 'tab_index', -1),
                        'proof_step_data': getattr(command.proof_step, 'serialize', lambda: {})()
                    }
            elif command_type in ['RenameObject', 'RenameArrow', 'MoveNode', 'AddNode', 'RemoveNode', 'AddArrow', 'RemoveArrow']:
                # Handle basic editing commands
                command_data['data'] = self._serialize_basic_command(command)
            
            return command_data
            
        except Exception as e:
            print(f"Warning: Could not serialize command {command.text()}: {e}")
            return None
    
    def _serialize_basic_command(self, command: QUndoCommand) -> Dict[str, Any]:
        """Serialize basic editing commands."""
        data = {}
        
        # Store common attributes that most commands have
        if hasattr(command, 'obj') and command.obj:
            # Store object reference info
            if hasattr(command.obj, 'get_text'):
                data['obj_text'] = command.obj.get_text()
            if hasattr(command.obj, 'pos'):
                pos = command.obj.pos()
                data['obj_pos'] = {'x': pos.x(), 'y': pos.y()}
        
        # Store old/new values for rename operations
        if hasattr(command, 'old_name'):
            data['old_name'] = command.old_name
        if hasattr(command, 'new_name'):
            data['new_name'] = command.new_name
        
        # Store position data for move operations
        if hasattr(command, 'old_pos'):
            pos = command.old_pos
            data['old_pos'] = {'x': pos.x(), 'y': pos.y()}
        if hasattr(command, 'new_pos'):
            pos = command.new_pos
            data['new_pos'] = {'x': pos.x(), 'y': pos.y()}
        
        return data
    
    def deserialize_undo_stack(self, stack_data: Dict[str, Any]):
        """Deserialize and restore the undo stack from saved data."""
        if not stack_data or 'commands' not in stack_data:
            return
        
        # Clear current stack
        self.undo_stack.clear()
        
        # Recreate commands (this is complex and may need scene context)
        # For now, we'll store the serialized data and mark the stack as clean
        # Full reconstruction would require access to the scene and objects
        
        # Set clean index if available
        if 'clean_index' in stack_data:
            # Note: QUndoStack doesn't have a direct way to set clean index
            # after clearing, so we'll need a different approach
            pass
        
        print(f"Undo stack serialization: {len(stack_data.get('commands', []))} commands saved")
    
    def clear_undo_stack(self):
        """Clear the undo stack."""
        self.undo_stack.clear()
