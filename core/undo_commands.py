"""
Undo commands for the Pythom DAG diagram editor.
"""
from PyQt6.QtGui import QUndoCommand
from PyQt6.QtCore import QPointF
from .proof_step import ProofStep


class ProofStepCommand(QUndoCommand):
    """Command to execute and undo proof steps."""
    
    def __init__(self, proof_step: ProofStep, description: str = None):
        description = description or f"Apply {proof_step.__class__.__name__}"
        super().__init__(description)
        self.proof_step = proof_step
        self.tab_index = proof_step.get_affected_tab_index()
    
    def redo(self):
        """Execute the proof step and switch to the appropriate tab."""
        # Switch to the tab where this proof step applies
        self._switch_to_tab()
        
        # Execute the proof step
        self.proof_step.apply()
    
    def undo(self):
        """Undo the proof step and switch to the appropriate tab."""
        # Switch to the tab where this proof step applies
        self._switch_to_tab()
        
        # Undo the proof step
        self.proof_step.unapply()
    
    def _switch_to_tab(self):
        """Switch to the tab where this proof step applies."""
        if self.tab_index >= 0:
            # Find the main window and switch tabs
            scene = self.proof_step.scene
            if hasattr(scene, 'parent') and scene.parent():
                main_window = scene.parent()
                if hasattr(main_window, 'tab_widget'):
                    main_window.tab_widget.setCurrentIndex(self.tab_index)


class RenameObject(QUndoCommand):
    """Command to rename an object node."""
    
    def __init__(self, obj, old_name, new_name):
        super().__init__(f"Rename Object '{old_name}' to '{new_name}'")
        self.obj = obj
        self.old_name = old_name
        self.new_name = new_name
    
    def redo(self):
        """Execute the rename."""
        self.obj.set_base_name(self.new_name)
    
    def undo(self):
        """Undo the rename."""
        self.obj.set_base_name(self.old_name)


class RenameArrow(QUndoCommand):
    """Command to rename an arrow."""
    
    def __init__(self, arrow, old_name, new_name):
        super().__init__(f"Rename Arrow '{old_name}' to '{new_name}'")
        self.arrow = arrow
        self.old_name = old_name
        self.new_name = new_name
    
    def redo(self):
        """Execute the rename."""
        self.arrow.set_base_name(self.new_name)
    
    def undo(self):
        """Undo the rename."""
        self.arrow.set_base_name(self.old_name)


class MoveObject(QUndoCommand):
    """Command to move an object node."""
    
    def __init__(self, obj, old_position, new_position):
        super().__init__(f"Move Object '{obj.get_text()}'")
        self.obj = obj
        self.old_position = old_position
        self.new_position = new_position
    
    def redo(self):
        """Execute the move."""
        self.obj.setPos(self.new_position)
    
    def undo(self):
        """Undo the move."""
        self.obj.setPos(self.old_position)


class PlaceObject(QUndoCommand):
    """Command to place an object node."""
    
    def __init__(self, scene, obj, position):
        super().__init__(f"Place Object '{obj.get_text()}'")
        self.scene = scene
        self.obj = obj
        self.position = position
    
    def redo(self):
        """Execute the placement."""
        self.scene.addItem(self.obj)
        self.obj.setPos(self.position)
    
    def undo(self):
        """Undo the placement."""
        self.scene.removeItem(self.obj)


class PlaceArrow(QUndoCommand):
    """Command to place an arrow."""
    
    def __init__(self, scene, arrow, start_node, end_node):
        super().__init__(f"Place Arrow '{arrow.get_text()}'")
        self.scene = scene
        self.arrow = arrow
        self.start_node = start_node
        self.end_node = end_node
    
    def redo(self):
        """Execute the placement."""
        # Set arrow endpoints and add to scene
        self.arrow.set_nodes(self.start_node, self.end_node)
        self.scene.addItem(self.arrow)
        
        # Update parallel arrows and self-loops
        from widget.arrow import Arrow
        Arrow.update_parallel_arrows_in_scene(self.scene)
        if self.start_node:
            Arrow.update_self_loops_for_node(self.start_node)
        if self.end_node and self.end_node != self.start_node:
            Arrow.update_self_loops_for_node(self.end_node)
    
    def undo(self):
        """Undo the placement."""
        self.scene.removeItem(self.arrow)
        
        # Update parallel arrows and self-loops after removal
        from widget.arrow import Arrow
        Arrow.update_parallel_arrows_in_scene(self.scene)
        if self.start_node:
            Arrow.update_self_loops_for_node(self.start_node)
        if self.end_node and self.end_node != self.start_node:
            Arrow.update_self_loops_for_node(self.end_node)


class DeleteItems(QUndoCommand):
    """Command to delete multiple items (objects and arrows)."""
    
    def __init__(self, scene, items):
        if len(items) == 1:
            item_name = items[0].get_text() if hasattr(items[0], 'get_text') else str(items[0])
            super().__init__(f"Delete {item_name}")
        else:
            super().__init__(f"Delete {len(items)} items")
        
        self.scene = scene
        self.item_data = []
        
        # Store item data for restoration
        from widget.object_node import Object
        from widget.arrow import Arrow
        
        for item in items:
            data = {'item': item}
            
            # Store position for objects
            if isinstance(item, Object):
                data['position'] = item.pos()
            
            # Store connections for arrows
            elif isinstance(item, Arrow):
                data['position'] = item.pos()
                data['source'] = item.get_source() if hasattr(item, 'get_source') else None
                data['target'] = item.get_target() if hasattr(item, 'get_target') else None
            
            self.item_data.append(data)
        
        # Also collect any arrows that will be deleted due to cascade
        self.cascade_arrows = []
        for item in items:
            if isinstance(item, Object):
                # Find arrows connected to this object
                for scene_item in scene.items():
                    if isinstance(scene_item, Arrow):
                        if (scene_item.get_source() == item or 
                            scene_item.get_target() == item) and scene_item not in items:
                            arrow_data = {
                                'item': scene_item,
                                'position': scene_item.pos(),
                                'source': scene_item.get_source(),
                                'target': scene_item.get_target()
                            }
                            self.cascade_arrows.append(arrow_data)
    
    def redo(self):
        """Execute the deletion."""
        from widget.arrow import Arrow
        
        # Clean up signal connections before removing cascade arrows
        for data in self.cascade_arrows:
            arrow = data['item']
            if arrow.scene() == self.scene:
                if hasattr(arrow, '_signal_cleanup'):
                    arrow._signal_cleanup()
                self.scene.removeItem(arrow)
        
        # Clean up signal connections before removing selected items
        for data in self.item_data:
            item = data['item']
            if item.scene() == self.scene:
                if hasattr(item, '_signal_cleanup'):
                    item._signal_cleanup()
                self.scene.removeItem(item)
        
        # Update parallel arrows and self-loops after deletion
        Arrow.update_parallel_arrows_in_scene(self.scene)
        
        # Update self-loops for any remaining connected nodes
        for data in self.item_data + self.cascade_arrows:
            if 'source' in data and data['source'] and data['source'].scene() == self.scene:
                Arrow.update_self_loops_for_node(data['source'])
            if 'target' in data and data['target'] and data['target'].scene() == self.scene:
                Arrow.update_self_loops_for_node(data['target'])
    
    def undo(self):
        """Undo the deletion."""
        from widget.object_node import Object
        from widget.arrow import Arrow
        
        # Restore original items first
        for data in self.item_data:
            item = data['item']
            if isinstance(item, Object):
                # Add item back to scene
                self.scene.addItem(item)
                
                # Restore position
                if data['position'] is not None:
                    item.setPos(data['position'])
            
            elif isinstance(item, Arrow):
                # Add item back to scene
                self.scene.addItem(item)
                
                # Restore position
                if data['position'] is not None:
                    item.setPos(data['position'])
                
                # Restore arrow connections
                if 'source' in data and 'target' in data:
                    if hasattr(item, 'set_nodes'):
                        item.set_nodes(data['source'], data['target'])
                
                # Set up signal connections for restored arrow
                if hasattr(item, '_signal_setup'):
                    item._signal_setup()
        
        # Restore cascade arrows
        for data in self.cascade_arrows:
            item = data['item']
            if isinstance(item, Arrow):
                # Add item back to scene
                self.scene.addItem(item)
                
                # Restore position
                if data['position'] is not None:
                    item.setPos(data['position'])
                
                # Restore arrow connections
                if 'source' in data and 'target' in data:
                    if hasattr(item, 'set_nodes'):
                        item.set_nodes(data['source'], data['target'])
                
                # Set up signal connections for restored cascade arrow
                if hasattr(item, '_signal_setup'):
                    item._signal_setup()
        
        # Update parallel arrows and self-loops after restoration
        Arrow.update_parallel_arrows_in_scene(self.scene)
        
        # Update self-loops for any connected nodes
        for data in self.item_data:
            if 'source' in data and data['source']:
                Arrow.update_self_loops_for_node(data['source'])
            if 'target' in data and data['target'] and data['target'] != data.get('source'):
                Arrow.update_self_loops_for_node(data['target'])


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


class CreateMappedElementCommand(QUndoCommand):
    """Command to create a mapped element f(x) in the codomain of an arrow f."""
    
    def __init__(self, scene, arrow, element_name, function_name):
        super().__init__(f"Map element {element_name} via {function_name}")
        self.scene = scene
        self.arrow = arrow
        self.element_name = element_name
        self.function_name = function_name
        self.created_object = None
        
    def redo(self):
        """Create the mapped element in the codomain."""
        if self.created_object is None:
            # Create new object in the codomain
            from widget.object_node import Object
            
            # Get the target (codomain) node
            target_node = self.arrow.get_target()
            if not target_node:
                return
                
            # Position the new element near the target node
            target_pos = target_node.pos()
            new_pos = QPointF(target_pos.x() + 100, target_pos.y() + 50)
            
            # Create the mapped element with name f(x)
            mapped_name = f"{self.function_name}({self.element_name})"
            self.created_object = Object(text=mapped_name)
            self.created_object.setPos(new_pos)
            
            # Add to scene
            self.scene.addItem(self.created_object)
        else:
            # Re-add the object
            self.scene.addItem(self.created_object)
    
    def undo(self):
        """Remove the created mapped element."""
        if self.created_object:
            self.scene.removeItem(self.created_object)
