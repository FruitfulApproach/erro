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
        self.was_added = False
    
    def redo(self):
        """Execute the placement."""
        if not self.was_added:
            self.obj.setPos(self.position)
            self.scene.addItem(self.obj)
            self.scene.object_added.emit(self.obj)
            self.was_added = True
        else:
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
        self.was_added = False
    
    def redo(self):
        """Execute the placement."""
        if not self.was_added:
            self.arrow.set_nodes(self.start_node, self.end_node)
            self.scene.addItem(self.arrow)
            self.was_added = True
        else:
            self.scene.addItem(self.arrow)
            self.arrow.set_nodes(self.start_node, self.end_node)
        
        # Update self-loops for connected nodes when a new arrow is placed
        from arrow import Arrow
        if self.start_node:
            Arrow.update_self_loops_for_node(self.start_node)
        if self.end_node and self.end_node != self.start_node:
            Arrow.update_self_loops_for_node(self.end_node)
        
        # Update parallel arrow curves for the entire scene
        Arrow.update_parallel_arrows_in_scene(self.scene)
    
    def undo(self):
        """Undo the placement."""
        self.scene.removeItem(self.arrow)
        
        # Update self-loops for connected nodes when an arrow is removed
        from arrow import Arrow
        if self.start_node:
            Arrow.update_self_loops_for_node(self.start_node)
        if self.end_node and self.end_node != self.start_node:
            Arrow.update_self_loops_for_node(self.end_node)
        
        # Update parallel arrow curves for the entire scene
        Arrow.update_parallel_arrows_in_scene(self.scene)


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


class PlaceLabel(QUndoCommand):
    """Command to place an additional label."""
    
    def __init__(self, scene, label, position):
        super().__init__(f"Place Label")
        self.scene = scene
        self.label = label
        self.position = position
        self.was_added = False
    
    def redo(self):
        """Execute the placement."""
        if not self.was_added:
            self.label.setPos(self.position)
            self.scene.addItem(self.label)
            self.was_added = True
        else:
            self.scene.addItem(self.label)
            self.label.setPos(self.position)
    
    def undo(self):
        """Undo the placement."""
        self.scene.removeItem(self.label)


class DeleteLabel(QUndoCommand):
    """Command to delete an additional label."""
    
    def __init__(self, scene, label):
        super().__init__(f"Delete Label")
        self.scene = scene
        self.label = label
        self.position = label.pos()
    
    def redo(self):
        """Execute the deletion."""
        self.scene.removeItem(self.label)
    
    def undo(self):
        """Undo the deletion."""
        self.scene.addItem(self.label)
        self.label.setPos(self.position)


class DeleteItems(QUndoCommand):
    """Command to delete selected items from the scene."""
    
    def __init__(self, scene, items_to_delete):
        self.scene = scene
        
        # Expand items to include connected arrows when deleting nodes
        self.items_to_delete = self._expand_deletion_set(items_to_delete)
        
        # Create description based on what's being deleted
        if len(self.items_to_delete) == 1:
            item = self.items_to_delete[0]
            if hasattr(item, 'get_text'):  # Object or Arrow
                item_type = "Object" if hasattr(item, 'boundingRect') and item.type() == 65537 else "Arrow"
                super().__init__(f"Delete {item_type} '{item.get_text()}'")
            else:
                super().__init__(f"Delete Item")
        else:
            # Count objects and arrows separately
            objects = [item for item in self.items_to_delete if hasattr(item, 'boundingRect') and item.type() == 65537]
            arrows = [item for item in self.items_to_delete if hasattr(item, 'get_source') and hasattr(item, 'get_target')]
            
            if objects and arrows:
                super().__init__(f"Delete {len(objects)} Object(s) and {len(arrows)} Arrow(s)")
            elif objects:
                super().__init__(f"Delete {len(objects)} Object(s)")
            elif arrows:
                super().__init__(f"Delete {len(arrows)} Arrow(s)")
            else:
                super().__init__(f"Delete {len(self.items_to_delete)} Items")
        
        # Store item data for restoration
        self.item_data = []
        for item in self.items_to_delete:
            data = {
                'item': item,
                'position': item.pos() if hasattr(item, 'pos') else None,
                'parent': item.parentItem() if hasattr(item, 'parentItem') else None
            }
            
            # Store connections for arrows
            if hasattr(item, 'get_source') and hasattr(item, 'get_target'):
                data['source'] = item.get_source()
                data['target'] = item.get_target()
            
            self.item_data.append(data)
    
    def _expand_deletion_set(self, items_to_delete):
        """
        Expand the deletion set to include connected arrows when deleting nodes.
        """
        from arrow import Arrow
        from object_node import Object
        
        expanded_set = set(items_to_delete)
        
        # Find all nodes being deleted
        nodes_to_delete = {item for item in items_to_delete if isinstance(item, Object)}
        
        if nodes_to_delete:
            # Find all arrows connected to these nodes
            for item in self.scene.items():
                if isinstance(item, Arrow):
                    source = item.get_source()
                    target = item.get_target()
                    
                    # If either source or target is being deleted, include the arrow
                    if (source in nodes_to_delete or target in nodes_to_delete):
                        expanded_set.add(item)
        
        return list(expanded_set)
    
    def redo(self):
        """Execute the deletion."""
        from arrow import Arrow
        
        # Remove items from scene
        for data in self.item_data:
            item = data['item']
            if item.scene():
                self.scene.removeItem(item)
        
        # Update parallel arrows and self-loops after deletion
        Arrow.update_parallel_arrows_in_scene(self.scene)
        
        # Update self-loops for any connected nodes
        for data in self.item_data:
            if 'source' in data and data['source']:
                Arrow.update_self_loops_for_node(data['source'])
            if 'target' in data and data['target'] and data['target'] != data.get('source'):
                Arrow.update_self_loops_for_node(data['target'])
    
    def undo(self):
        """Undo the deletion."""
        from arrow import Arrow
        
        # Restore items to scene in correct order (nodes first, then arrows)
        from object_node import Object
        
        # First, restore all nodes
        for data in self.item_data:
            item = data['item']
            if isinstance(item, Object):
                # Add item back to scene
                self.scene.addItem(item)
                
                # Restore position
                if data['position'] is not None:
                    item.setPos(data['position'])
        
        # Then, restore all arrows
        for data in self.item_data:
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
 
  
 c l a s s   F l i p A r r o w C o m m a n d ( Q U n d o C o m m a n d ) :  
         " " " C o m m a n d   t o   f l i p   t h e   d i r e c t i o n   o f   a n   a r r o w   b y   s w a p p i n g   s o u r c e   a n d   t a r g e t . " " "  
  
         d e f   _ _ i n i t _ _ ( s e l f ,   a r r o w ) :  
                 s u p e r ( ) . _ _ i n i t _ _ ( f \  
 F l i p  
 A r r o w  
 { a r r o w . g e t _ t e x t ( ) }  
 \ )  
                 s e l f . a r r o w   =   a r r o w  
                 s e l f . o r i g i n a l _ s o u r c e   =   a r r o w . g e t _ s o u r c e ( )  
                 s e l f . o r i g i n a l _ t a r g e t   =   a r r o w . g e t _ t a r g e t ( )  
  
         d e f   r e d o ( s e l f ) :  
                 " " " E x e c u t e   t h e   f l i p . " " "  
                 #   S w a p   t h e   s o u r c e   a n d   t a r g e t   n o d e s  
                 s e l f . a r r o w . s e t _ n o d e s ( s e l f . o r i g i n a l _ t a r g e t ,   s e l f . o r i g i n a l _ s o u r c e )  
  
         d e f   u n d o ( s e l f ) :  
                 " " " U n d o   t h e   f l i p . " " "  
                 #   R e s t o r e   t h e   o r i g i n a l   s o u r c e   a n d   t a r g e t  
 