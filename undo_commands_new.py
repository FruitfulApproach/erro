"""
Undo commands for the Pythom DAG diagram editor.
"""
from PyQt6.QtGui import QUndoCommand
from PyQt6.QtCore import QPointF


class RenameObject(QUndoCommand):
    """Command to rename an object node."""
    
    def __init__(self, obj, old_name, new_name):
        super().__init__(f"Rename Object '{old_name}' to '{new_name}'")
        self.obj = obj
        self.old_name = old_name
        self.new_name = new_name
    
    def redo(self):
        """Execute the rename."""
        self.obj.set_text(self.new_name)
    
    def undo(self):
        """Undo the rename."""
        self.obj.set_text(self.old_name)


class RenameArrow(QUndoCommand):
    """Command to rename an arrow."""
    
    def __init__(self, arrow, old_name, new_name):
        super().__init__(f"Rename Arrow '{old_name}' to '{new_name}'")
        self.arrow = arrow
        self.old_name = old_name
        self.new_name = new_name
    
    def redo(self):
        """Execute the rename."""
        self.arrow.set_text(self.new_name)
    
    def undo(self):
        """Undo the rename."""
        self.arrow.set_text(self.old_name)


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
        from arrow import Arrow
        Arrow.update_parallel_arrows_in_scene(self.scene)
        if self.start_node:
            Arrow.update_self_loops_for_node(self.start_node)
        if self.end_node and self.end_node != self.start_node:
            Arrow.update_self_loops_for_node(self.end_node)
    
    def undo(self):
        """Undo the placement."""
        self.scene.removeItem(self.arrow)
        
        # Update parallel arrows and self-loops after removal
        from arrow import Arrow
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
        from object_node import Object
        from arrow import Arrow
        
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
        from arrow import Arrow
        
        # Remove cascade arrows first
        for data in self.cascade_arrows:
            arrow = data['item']
            if arrow.scene() == self.scene:
                self.scene.removeItem(arrow)
        
        # Remove the selected items
        for data in self.item_data:
            item = data['item']
            if item.scene() == self.scene:
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
        from object_node import Object
        from arrow import Arrow
        
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
