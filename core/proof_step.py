"""
Abstract base class for proof steps in diagram transformations.
"""
from abc import ABC, abstractmethod
from typing import List, Any
from PyQt6.QtCore import QPointF


class ProofStep(ABC):
    """Abstract base class for proof steps that can be applied to diagrams."""
    
    def __init__(self, scene):
        """Initialize the proof step with a reference to the scene."""
        self.scene = scene
    
    @staticmethod
    @abstractmethod
    def is_applicable(objects: List[Any], arrows: List[Any]) -> bool:
        """
        Check if this proof step is applicable to the given objects and arrows.
        
        Args:
            objects: List of selected objects in the diagram
            arrows: List of selected arrows in the diagram
            
        Returns:
            bool: True if this proof step can be applied, False otherwise
        """
        pass
    
    @staticmethod
    @abstractmethod
    def button_text(objects: List[Any], arrows: List[Any]) -> str:
        """
        Get the button text to display for this proof step.
        
        Args:
            objects: List of selected objects in the diagram
            arrows: List of selected arrows in the diagram
            
        Returns:
            str: The text to display on the button
        """
        pass
    
    @abstractmethod
    def apply(self) -> None:
        """
        Apply this proof step to the diagram.
        This method should perform the transformation and store any data
        needed for unapply().
        """
        pass
    
    @abstractmethod
    def unapply(self) -> None:
        """
        Unapply this proof step, reverting the diagram to its previous state.
        This method should restore the diagram to the state before apply() was called.
        """
        pass
    
    def get_affected_tab_index(self) -> int:
        """
        Get the tab index where this proof step will take effect.
        
        Returns:
            int: The tab index, or -1 if not applicable
        """
        # Find the tab that contains this scene
        if hasattr(self.scene, 'parent') and self.scene.parent():
            main_window = self.scene.parent()
            if hasattr(main_window, 'tab_widget'):
                for i in range(main_window.tab_widget.count()):
                    view = main_window.tab_widget.widget(i)
                    if view and view.scene() == self.scene:
                        return i
        return -1

    def _check_auto_grid_spacing(self):
        """Check and adjust grid spacing if auto-spacing is enabled.
        
        NOTE: This method is disabled during proof step execution to prevent 
        unwanted node movement. ProofSteps should never move nodes.
        """
        # Disabled to prevent node movement during proof step execution
        return


class IdentityProofStep(ProofStep):
    """Proof step that creates a duplicate object with identity morphism arrow."""
    
    def __init__(self, scene, objects, arrows):
        super().__init__(scene)
        self.objects = objects
        self.arrows = arrows
        self.created_object = None
        self.created_arrow = None
    
    @staticmethod
    def is_applicable(objects: List[Any], arrows: List[Any]) -> bool:
        """Applicable when exactly 1 object is selected."""
        return len(objects) == 1 and len(arrows) == 0
    
    @staticmethod
    def button_text(objects: List[Any], arrows: List[Any]) -> str:
        """Return the button text for this proof step."""
        obj_name = objects[0].get_text() if objects else "Object"
        return f"🔁 Identity on {obj_name}"
    
    def _create_unicode_subscript(self, text: str) -> str:
        """Create unicode subscript for identity arrow label."""
        # Unicode subscript mapping
        subscript_map = {
            '0': '₀', '1': '₁', '2': '₂', '3': '₃', '4': '₄',
            '5': '₅', '6': '₆', '7': '₇', '8': '₈', '9': '₉',
            'a': 'ₐ', 'e': 'ₑ', 'h': 'ₕ', 'i': 'ᵢ', 'j': 'ⱼ',
            'k': 'ₖ', 'l': 'ₗ', 'm': 'ₘ', 'n': 'ₙ', 'o': 'ₒ',
            'p': 'ₚ', 'r': 'ᵣ', 's': 'ₛ', 't': 'ₜ', 'u': 'ᵤ',
            'v': 'ᵥ', 'x': 'ₓ'
        }
        
        # Try to convert to unicode subscript
        subscript_text = ""
        can_convert_all = True
        
        for char in text:  # Don't convert to lowercase!
            if char in subscript_map:
                subscript_text += subscript_map[char]
            else:
                can_convert_all = False
                break
        
        if can_convert_all:
            return f"𝟏{subscript_text}"
        elif len(text) == 1:
            return f"𝟏({text})"
        else:
            return f"𝟏({text})"
    
    def apply(self) -> None:
        """Create duplicate object and identity arrow."""
        if not self.objects:
            return
        
        original_obj = self.objects[0]
        original_name = original_obj.get_text()
        
        # Import the classes we need
        from widget.object_node import Object
        from widget.arrow import Arrow
        
        # Create duplicate object with same name
        self.created_object = Object(original_name)
        
        # Position the new object to the right of the original
        original_pos = original_obj.pos()
        offset_x = 150  # Distance to the right
        new_pos = original_pos + type(original_pos)(offset_x, 0)
        self.created_object.setPos(new_pos)
        
        # Add the new object to the scene
        self.scene.addItem(self.created_object)
        
        # Create identity arrow from original to duplicate
        self.created_arrow = Arrow(original_obj, self.created_object)
        
        # Set the arrow label with unicode subscript
        identity_label = self._create_unicode_subscript(original_name)
        self.created_arrow.set_text(identity_label)
        
        # Add the arrow to the scene
        self.scene.addItem(self.created_arrow)
        
        # Set up signal connections for identity arrow
        self.created_arrow._signal_setup()
        
        # Update parallel arrows positioning
        from widget.arrow import Arrow
        Arrow.update_parallel_arrows_in_scene(self.scene)
        
        # Update the scene
        self.scene.update()
    
    def unapply(self) -> None:
        """Remove the created object and arrow."""
        if self.created_arrow and self.created_arrow.scene():
            # Clean up signal connections before removing
            self.created_arrow._signal_cleanup()
            self.scene.removeItem(self.created_arrow)
        
        if self.created_object and self.created_object.scene():
            self.scene.removeItem(self.created_object)
        
        # Update parallel arrows positioning after removal
        from widget.arrow import Arrow
        Arrow.update_parallel_arrows_in_scene(self.scene)
        
        # Clear references
        self.created_arrow = None
        self.created_object = None
        
        # Update the scene
        self.scene.update()


class CompositionProofStep(ProofStep):
    """Proof step for function composition when two arrows are in sequence."""
    
    def __init__(self, scene, objects, arrows):
        super().__init__(scene)
        self.objects = objects
        self.arrows = arrows
        self.composed_arrow = None
        self.original_arrows = []
    
    @staticmethod
    def is_applicable(objects: List[Any], arrows: List[Any]) -> bool:
        """Applicable when exactly 2 arrows are selected and they can be composed."""
        if len(arrows) != 2:
            return False
        
        arrow1, arrow2 = arrows[0], arrows[1]
        
        # Check if arrows can be composed (end of one connects to start of other)
        return (arrow1.get_target() == arrow2.get_source() or 
                arrow2.get_target() == arrow1.get_source())
    
    @staticmethod
    def button_text(objects: List[Any], arrows: List[Any]) -> str:
        """Return the button text for this proof step."""
        return "∘ Compose Arrows"
    
    def apply(self) -> None:
        """Create a composed arrow while preserving the original arrows."""
        if len(self.arrows) == 2:
            arrow1, arrow2 = self.arrows[0], self.arrows[1]
            
            # Determine composition order
            if arrow1.get_target() == arrow2.get_source():
                # arrow1 -> arrow2: composition is arrow2∘arrow1 (second composed with first)
                start_node = arrow1.get_source()
                end_node = arrow2.get_target()
                comp_text = f"{arrow2.get_text()}∘{arrow1.get_text()}"
            else:
                # arrow2 -> arrow1: composition is arrow1∘arrow2 (first composed with second)
                start_node = arrow2.get_source()
                end_node = arrow1.get_target()
                comp_text = f"{arrow1.get_text()}∘{arrow2.get_text()}"
            
            # Store reference to original arrows (but don't remove them)
            self.original_arrows = [arrow1, arrow2]
            
            # Create composed arrow without removing originals
            from widget.arrow import Arrow
            self.composed_arrow = Arrow(start_node, end_node, comp_text)
            self.scene.addItem(self.composed_arrow)
            
            # Set up signal connections for composition arrow
            self.composed_arrow._signal_setup()
            
            # Update parallel arrows positioning
            from widget.arrow import Arrow
            Arrow.update_parallel_arrows_in_scene(self.scene)
    
    def unapply(self) -> None:
        """Remove the composed arrow (original arrows are preserved)."""
        if self.composed_arrow:
            # Clean up signal connections before removing
            self.composed_arrow._signal_cleanup()
            self.scene.removeItem(self.composed_arrow)
            self.composed_arrow = None
            
            # Update parallel arrows positioning after removal
            from widget.arrow import Arrow
            Arrow.update_parallel_arrows_in_scene(self.scene)


class CancelIdentityProofStep(ProofStep):
    """Proof step that cancels identity morphisms from arrow labels."""
    
    @staticmethod
    def is_applicable(objects: List[Any], arrows: List[Any]) -> bool:
        """Applicable when exactly 1 arrow is selected and it contains identity morphisms in a composition."""
        if len(arrows) != 1:
            return False
        
        arrow = arrows[0]
        text = arrow.get_text()
        
        # Must contain at least one identity morphism
        if '𝟏(' not in text:
            return False
        
        # But must NOT be a pure identity morphism (like "𝟏(X)")
        import re
        if re.match(r'^𝟏\([^∘)]+\)$', text.strip()):
            return False  # Pure identity, nothing to cancel
        
        return True  # Has identities in composition, can cancel them
    
    @staticmethod
    def button_text(objects: List[Any], arrows: List[Any]) -> str:
        """Return the text for the proof step button."""
        return "✂️ Cancel Identities"
    
    def __init__(self, scene, objects, arrows):
        """
        Initialize with scene and selected items.
        
        Args:
            scene: The diagram scene
            objects: List of selected objects
            arrows: List of selected arrows (should contain exactly 1 arrow with identities)
        """
        super().__init__(scene)
        self.objects = objects
        self.arrows = arrows
        self.arrow = arrows[0] if arrows else None  # Get the single selected arrow
        self.original_text = self.arrow.get_text() if self.arrow else ""
        self.new_text = None
        
    def _cancel_identities(self, text: str) -> str:
        """
        Remove identity morphisms and adjacent composition symbols.
        
        Examples:
            "f∘g∘𝟏(A)∘h" -> "f∘g∘h"
            "𝟏(X)∘f∘g" -> "f∘g"  
            "f∘g∘𝟏(Y)" -> "f∘g"
            "f∘𝟏(A)∘g∘h" -> "f∘g∘h"
            "𝟏(X)" -> "𝟏(X)" (no change - pure identity)
        """
        import re
        
        # Check if this is a pure identity morphism (just "𝟏(X)" with no composition)
        if re.match(r'^𝟏\([^∘)]+\)$', text.strip()):
            # This is a pure identity morphism, don't cancel it
            return text
        
        # Pattern to match identity morphism with composition symbols
        # This matches: ∘𝟏(<anything>)∘ OR ∘𝟏(<anything>) OR 𝟏(<anything>)∘
        pattern = r'(∘𝟏\([^)]+\)∘|∘𝟏\([^)]+\)$|^𝟏\([^)]+\)∘)'
        
        # Keep removing until no more identities found
        while True:
            original = text
            
            # Remove identity with composition symbols on both sides: ∘𝟏(X)∘ -> ∘
            text = re.sub(r'∘𝟏\([^)]+\)∘', '∘', text)
            
            # Remove identity at the beginning with composition: 𝟏(X)∘ -> (empty)
            text = re.sub(r'^𝟏\([^)]+\)∘', '', text)
            
            # Remove identity at the end with composition: ∘𝟏(X) -> (empty)  
            text = re.sub(r'∘𝟏\([^)]+\)$', '', text)
            
            # Remove standalone identity: 𝟏(X) -> (empty)
            text = re.sub(r'^𝟏\([^)]+\)$', '', text)
            
            # If no changes were made, we're done
            if text == original:
                break
                
        return text
    
    def get_description(self) -> str:
        """Get a human-readable description of this proof step."""
        return f"Cancel identity morphisms in '{self.original_text}'"
        
    def apply(self) -> None:
        """Cancel identity morphisms from the arrow label."""
        self.new_text = self._cancel_identities(self.original_text)
        self.arrow.set_text(self.new_text)
        
    def unapply(self) -> None:
        """Restore the original arrow label."""
        self.arrow.set_text(self.original_text)


class TakeKernelProofStep(ProofStep):
    """Proof step that creates a kernel object and morphism for a selected arrow."""
    
    def __init__(self, scene, objects, arrows):
        super().__init__(scene)
        self.objects = objects
        self.arrows = arrows
        self.arrow = arrows[0] if arrows else None
        self.kernel_object = None
        self.kernel_arrow = None
        
    @staticmethod
    def is_applicable(objects: List[Any], arrows: List[Any]) -> bool:
        """This step is applicable when exactly 1 arrow is selected."""
        return len(objects) == 0 and len(arrows) == 1
    
    @staticmethod
    def button_text(objects: List[Any], arrows: List[Any]) -> str:
        """Return the button text for this proof step."""
        if arrows and len(arrows) == 1:
            arrow_text = arrows[0].get_text()
            return f"🔽 Take Ker({arrow_text})"
        return "🔽 Take Kernel"
    
    def apply(self) -> None:
        """Create kernel object and morphism."""
        if not self.arrow:
            return
        
        # Get the source node of the original arrow
        source_node = self.arrow._start_node
        
        # Create kernel object name (Ker e) - using normal text
        arrow_text = self.arrow.get_text()
        kernel_name = f"Ker {arrow_text}"
        
        # Position the kernel object - find closest open grid point
        source_pos = source_node.pos()
        grid_size = getattr(self.scene, '_grid_size', 50)
        
        # Try positions in order of preference: left, right, top, bottom
        potential_positions = [
            QPointF(source_pos.x() - grid_size, source_pos.y()),      # Left
            QPointF(source_pos.x() + grid_size, source_pos.y()),      # Right  
            QPointF(source_pos.x(), source_pos.y() - grid_size),      # Top
            QPointF(source_pos.x(), source_pos.y() + grid_size),      # Bottom
        ]
        
        kernel_pos = None
        # Check if position is occupied and find nearest free position
        if hasattr(self.scene, '_is_grid_position_occupied'):
            for pos in potential_positions:
                snapped_pos = self.scene.snap_to_grid(pos)
                if not self.scene._is_grid_position_occupied(snapped_pos):
                    kernel_pos = snapped_pos
                    break
            
            # If all close positions are occupied, find any nearest free position
            if kernel_pos is None:
                kernel_pos = self.scene._find_nearest_free_grid_position(potential_positions[0])
        else:
            # Fallback if no grid checking available
            kernel_pos = potential_positions[0]
        
        # Create kernel object
        from widget.object_node import Object
        self.kernel_object = Object(kernel_name)
        self.kernel_object.setPos(kernel_pos)
        self.scene.addItem(self.kernel_object)
        
        # Create kernel arrow 𝐤(f) : �er f -> A (keeping parentheses format for clarity)
        from widget.arrow import Arrow
        kernel_arrow_name = f"𝐤({arrow_text})"
        self.kernel_arrow = Arrow(self.kernel_object, source_node, kernel_arrow_name)
        
        # Kernel arrows are automatically inclusions and this cannot be changed
        self.kernel_arrow.set_as_kernel_arrow()
        
        self.scene.addItem(self.kernel_arrow)
        
    def unapply(self) -> None:
        """Remove the kernel object and morphism."""
        if self.kernel_arrow:
            self.scene.removeItem(self.kernel_arrow)
            self.kernel_arrow = None
        if self.kernel_object:
            self.scene.removeItem(self.kernel_object)
            self.kernel_object = None


class TakeElementProofStep(ProofStep):
    """Proof step to take an element from an object in a concrete category."""
    
    def __init__(self, scene, selected_objects, selected_arrows):
        super().__init__(scene)
        self.obj = selected_objects[0] if selected_objects else None
        self.selected_objects = selected_objects
        self.selected_arrows = selected_arrows
        self.element_symbol = None
        self.original_text = None
    
    @classmethod
    def get_name(cls) -> str:
        """Return the human-readable name of this proof step."""
        return "📋 Take Element"
    
    @classmethod
    def get_description(cls) -> str:
        """Return a description of what this proof step does."""
        return "📋 Take an element from an object"
    
    @classmethod
    def is_applicable(cls, objects, arrows, scene=None) -> bool:
        """Return True if exactly one object is selected."""
        return len(objects) == 1 and len(arrows) == 0
    
    @staticmethod
    def button_text(objects, arrows) -> str:
        """Get the text to display on the proof step button."""
        if len(objects) == 1:
            obj = objects[0]
            return f"Take Element of {obj.get_text()}"
        return "Take Element"
    
    def apply(self) -> None:
        """Add an element symbol to the selected object."""
        if not self.obj:
            return
        
        # Show the element rename dialog
        from dialog.element_rename_dialog import ElementRenameDialog
        dialog = ElementRenameDialog()
        
        if dialog.exec() == dialog.DialogCode.Accepted:
            self.element_symbol = dialog.get_element_name()
            
            # Store original text for undo
            self.original_text = self.obj.get_display_text()
            
            # Replace display text with "element:ObjectName" format
            # but keep the base name unchanged
            base_name = self.obj.get_text()  # This returns the base name
            new_display_text = f"{self.element_symbol}:{base_name}"
            self.obj.set_text(new_display_text)  # Only changes display, not base name
            
            # Update connection points of all arrows connected to this object
            self._update_connected_arrows()
        else:
            # Dialog was cancelled
            raise Exception("Element dialog cancelled")
    
    def _update_connected_arrows(self):
        """Update connection points of all arrows connected to this object."""
        if not self.obj or not self.obj.scene():
            return
        
        # Find all arrows connected to this object
        for item in self.obj.scene().items():
            if hasattr(item, 'get_source') and hasattr(item, 'get_target'):
                # Check if this arrow is connected to our object
                if item.get_source() == self.obj or item.get_target() == self.obj:
                    item.update_position()
        
        # Check and adjust grid spacing if auto-spacing is enabled
        self._check_auto_grid_spacing()
    
    def unapply(self) -> None:
        """Remove the element symbol and restore original text."""
        if not self.obj or not hasattr(self, 'original_text'):
            return
        
            # Restore original text
            self.obj.set_text(self.original_text)


class MapElementProofStep(ProofStep):
    """Proof step to map an element from domain to codomain via an arrow."""
    
    def __init__(self, scene, selected_objects, selected_arrows):
        super().__init__(scene)
        self.arrow = selected_arrows[0] if selected_arrows else None
        self.selected_objects = selected_objects
        self.selected_arrows = selected_arrows
        self.element_name = None
        self.function_name = None
        self.created_object = None
    
    @classmethod
    def get_name(cls) -> str:
        """Return the human-readable name of this proof step."""
        return "🔀 Map Element"
    
    @classmethod
    def get_description(cls) -> str:
        """Return a description of what this proof step does."""
        return "🔀 Map an element from domain to codomain via a function"
    
    @classmethod
    def is_applicable(cls, objects, arrows, scene=None) -> bool:
        """Return True if exactly one arrow is selected and its domain contains a colon."""
        if len(arrows) != 1 or len(objects) != 0:
            return False
        
        arrow = arrows[0]
        domain_node = arrow.get_source()
        if not domain_node or not hasattr(domain_node, 'get_display_text'):
            return False
        
        # Check if domain's full text label (as displayed) contains a colon
        domain_text = domain_node.get_display_text()
        return ':' in domain_text
    
    @staticmethod
    def button_text(objects, arrows) -> str:
        """Get the text to display on the proof step button."""
        if len(arrows) == 1:
            arrow = arrows[0]
            function_name = arrow.get_text()
            return f"Map Element via {function_name}"
        return "Map Element"
    
    def apply(self) -> None:
        """Show element selection dialog (if needed) and modify codomain node."""
        if not self.arrow:
            return
        
        domain_node = self.arrow.get_source()
        codomain_node = self.arrow.get_target()
        
        if not domain_node or not codomain_node:
            return
        
        # Get domain text and function name
        domain_text = domain_node.get_display_text()
        self.function_name = self.arrow.get_text()
        
        # Store original codomain text for undo
        self.original_codomain_text = codomain_node.get_display_text()
        self.original_codomain_base_name = codomain_node.get_text()  # This returns base_name
        
        # Parse elements from domain text
        if ':' in domain_text:
            elements_part = domain_text.split(':', 1)[0]
        else:
            elements_part = domain_text
            
        # Split by comma and clean up whitespace
        elements = [elem.strip() for elem in elements_part.split(',') if elem.strip()]
        
        if len(elements) == 1:
            # Only one element - use it directly without dialog
            self.element_name = elements[0]
        elif len(elements) > 1:
            # Multiple elements - show selection dialog
            from dialog.element_select_dialog import ElementSelectDialog
            dialog = ElementSelectDialog(domain_text)
            
            if dialog.exec() == dialog.DialogCode.Accepted:
                self.element_name = dialog.get_selected_element()
            else:
                # Dialog was cancelled
                raise Exception("Element selection dialog cancelled")
        else:
            # No elements found
            raise Exception("No elements found in domain text")
        
        # Modify the codomain node if we have a selected element
        if self.element_name:
            # Get the codomain's current display text and extract base name
            current_codomain_text = codomain_node.get_display_text()
            
            # Extract the true base name from the display text
            if ':' in current_codomain_text:
                # For "x=y,z:C" format, base name is "C" (part after the colon)
                codomain_base_name = current_codomain_text.split(':', 1)[1].strip()
            else:
                # For simple object names like "D", base name is the whole text
                codomain_base_name = current_codomain_text.strip()
            
            # Handle composition notation properly
            mapped_element = self._create_mapped_element_notation(self.element_name, self.function_name)
            
            # Check if codomain already has elements (contains colon and elements before it)
            if ':' in current_codomain_text:
                # Extract existing elements part (left of colon)
                existing_elements = current_codomain_text.split(':', 1)[0].strip()
                if existing_elements:
                    # Prepend new mapped element to existing elements
                    new_display_text = f"{mapped_element},{existing_elements}:{codomain_base_name}"
                else:
                    # Colon exists but no elements before it
                    new_display_text = f"{mapped_element}:{codomain_base_name}"
            else:
                # No colon, treat as simple object name - add mapped element
                new_display_text = f"{mapped_element}:{codomain_base_name}"
            
            # Update the codomain node display text while preserving base name
            codomain_node.set_text(new_display_text)
            codomain_node._base_name = codomain_base_name
            
            # Update connection points of all arrows connected to the codomain object
            self._update_connected_arrows(codomain_node)
    
    def _create_mapped_element_notation(self, element_name, function_name):
        """Create proper function application notation for mapped elements, handling equalities."""
        # Check if this is an equality expression
        if '=' in element_name:
            return self._map_equality_expression(element_name, function_name)
        
        # Simple element - just concatenate
        return f"{function_name}{element_name}"
    
    def _map_equality_expression(self, equality_expr, function_name):
        """Map an equality expression, handling the special case where the whole expression equals zero."""
        # Check if the expression ends with =0 (the whole thing equals zero)
        if equality_expr.endswith('=0'):
            # This is like "Aa=0" - the whole "Aa" expression equals 0
            # When mapped by f, it becomes "fAa=0"
            base_expr = equality_expr[:-2]  # Remove "=0"
            return f"{function_name}{base_expr}=0"
        
        # Check if the expression starts with 0= (zero equals something)
        if equality_expr.startswith('0='):
            # This is like "0=B" - zero equals some expression B
            # When mapped by f, it becomes "0=fB"
            right_expr = equality_expr[2:]  # Remove "0="
            return f"0={function_name}{right_expr}"
        
        # General equality case: split on the first '=' and map both sides
        parts = equality_expr.split('=', 1)
        if len(parts) == 2:
            left_side = parts[0].strip()
            right_side = parts[1].strip()
            
            # Map both sides
            mapped_left = f"{function_name}{left_side}"
            mapped_right = f"{function_name}{right_side}"
            return f"{mapped_left}={mapped_right}"
        
        # Not a recognizable equality, fall back to regular mapping
        return f"{function_name}{equality_expr}"
    
    def _update_connected_arrows(self, node):
        """Update connection points of all arrows connected to the given node."""
        if not node or not node.scene():
            return
        
        # Find all arrows connected to this node
        for item in node.scene().items():
            if hasattr(item, 'get_source') and hasattr(item, 'get_target'):
                # Check if this arrow is connected to the node
                if item.get_source() == node or item.get_target() == node:
                    item.update_position()
        
        # Check and adjust grid spacing if auto-spacing is enabled
        self._check_auto_grid_spacing()
    
    def unapply(self) -> None:
        """Restore the original codomain node text."""
        if not self.arrow:
            return
            
        codomain_node = self.arrow.get_target()
        if not codomain_node:
            return
            
        # Restore original text and base name
        if hasattr(self, 'original_codomain_text'):
            codomain_node.set_text(self.original_codomain_text)
        if hasattr(self, 'original_codomain_base_name'):
            codomain_node._base_name = self.original_codomain_base_name


class KernelAtElementIsZeroProofStep(ProofStep):
    """Proof step to mark kernel elements as zero: (e∘𝐤(e))(a) = 𝟎."""
    
    def __init__(self, scene, selected_objects, selected_arrows):
        super().__init__(scene)
        self.node = selected_objects[0] if selected_objects else None
        self.selected_objects = selected_objects
        self.selected_arrows = selected_arrows
        self.original_text = None
        self.original_base_name = None
    
    @classmethod
    def get_name(cls) -> str:
        """Return the human-readable name of this proof step."""
        return "⚬ Kernel at Element is 0"
    
    @classmethod
    def get_description(cls) -> str:
        """Return a description of what this proof step does."""
        return "⚬ Mark kernel element as zero: (e∘𝐤(e))(a) = 𝟎"
    
    @classmethod
    def is_applicable(cls, objects, arrows, scene=None) -> bool:
        """Return True if exactly one object is selected and contains kernel element pattern."""
        if len(objects) != 1 or len(arrows) != 0:
            return False
        
        node = objects[0]
        if not hasattr(node, 'get_display_text'):
            return False
        
        display_text = node.get_display_text()
        
        # Check for pattern like "(e∘𝐤(e))(a)" where element contains kernel composition
        # Look for elements that have the pattern (e∘𝐤(e))(something)
        if ':' in display_text:
            elements_part = display_text.split(':', 1)[0]
            # Split by comma to handle multiple elements
            elements = [elem.strip() for elem in elements_part.split(',') if elem.strip()]
            
            for element in elements:
                if cls._is_kernel_element_pattern(element):
                    return True
        
        return False
    
    @classmethod
    def _is_kernel_element_pattern(cls, element):
        """Check if element matches strict kernel pattern (f∘𝐤(f))(a) where 𝐤(f) is kernel of f."""
        # Look for pattern containing ∘𝐤( which indicates kernel composition
        if '∘𝐤(' in element and '(' in element and ')' in element:
            # Extract the composition part before the final (a)
            last_paren = element.rfind('(')
            if last_paren == -1:
                return False
                
            composition_part = element[:last_paren]
            
            # Remove outer parentheses if present
            if composition_part.startswith('(') and composition_part.endswith(')'):
                composition_part = composition_part[1:-1]
            
            # Split by ∘ to get the functions
            functions = [f.strip() for f in composition_part.split('∘')]
            
            # Check if we have exactly 2 functions and the pattern is f∘𝐤(f)
            if len(functions) == 2:
                f_function = functions[0]  # First function (e.g., "e")
                kernel_function = functions[1]  # Second function (e.g., "𝐤(e)")
                
                # Check if kernel function has the form 𝐤(f) where f matches the first function
                if kernel_function.startswith('𝐤(') and kernel_function.endswith(')'):
                    inner_func = kernel_function[2:-1]  # Extract content between 𝐤( and )
                    if inner_func == f_function:
                        return True
        
        return False
    
    @staticmethod
    def button_text(objects, arrows) -> str:
        """Get the text to display on the proof step button."""
        return "Kernel at Element is 0"
    
    def apply(self) -> None:
        """Mark kernel elements as zero."""
        if not self.node:
            return
        
        # Store original text for undo
        self.original_text = self.node.get_display_text()
        self.original_base_name = self.node.get_text()
        
        display_text = self.node.get_display_text()
        
        if ':' in display_text:
            elements_part, base_part = display_text.split(':', 1)
            elements = [elem.strip() for elem in elements_part.split(',') if elem.strip()]
            
            # Transform kernel elements to zero
            transformed_elements = []
            for element in elements:
                if self._is_kernel_element_pattern(element):
                    # Transform (e∘𝐤(e))(a) to (e∘𝐤(e))(a)=𝟎
                    transformed_elements.append(f"{element}=𝟎")
                else:
                    transformed_elements.append(element)
            
            # Reconstruct the display text
            new_elements_part = ", ".join(transformed_elements)
            new_display_text = f"{new_elements_part}:{base_part}"
            
            # Update the node
            self.node.set_text(new_display_text)
            self.node._base_name = self.original_base_name
            
            # Update connection points of all arrows connected to this node
            self._update_connected_arrows()
    
    def _update_connected_arrows(self):
        """Update connection points of all arrows connected to this node."""
        if not self.node or not self.node.scene():
            return
        
        # Find all arrows connected to this node
        for item in self.node.scene().items():
            if hasattr(item, 'get_source') and hasattr(item, 'get_target'):
                # Check if this arrow is connected to the node
                if item.get_source() == self.node or item.get_target() == self.node:
                    item.update_position()
        
        # Check and adjust grid spacing if auto-spacing is enabled
        self._check_auto_grid_spacing()
    
    def unapply(self) -> None:
        """Restore the original node text."""
        if not self.node:
            return
            
        # Restore original text and base name
        if hasattr(self, 'original_text'):
            self.node.set_text(self.original_text)
        if hasattr(self, 'original_base_name'):
            self.node._base_name = self.original_base_name


class CompositionToApplicationProofStep(ProofStep):
    """Proof step that converts composition notation to function application notation."""
    
    def __init__(self, scene, selected_objects, selected_arrows):
        super().__init__(scene)
        self.node = selected_objects[0] if selected_objects else None
        self.selected_objects = selected_objects
        self.selected_arrows = selected_arrows
        self.original_text = None
        self.original_base_name = None
    
    @classmethod
    def get_name(cls) -> str:
        """Return the human-readable name of this proof step."""
        return "⚡ Composition to Application"
    
    @classmethod
    def get_description(cls) -> str:
        """Return a description of what this proof step does."""
        return "⚡ Convert (c∘b)da to cbda when both forms exist"
    
    @classmethod
    def is_applicable(cls, objects, arrows, scene=None) -> bool:
        """Return True if exactly one object is selected and contains composition elements."""
        if len(objects) != 1 or len(arrows) != 0:
            return False
        
        node = objects[0]
        if not hasattr(node, 'get_display_text'):
            return False
        
        display_text = node.get_display_text()
        
        # Check if the node contains elements with composition notation
        if ':' in display_text:
            elements_part = display_text.split(':', 1)[0]
            elements = [elem.strip() for elem in elements_part.split(',') if elem.strip()]
            
            # Look for composition elements like (c∘b)da and corresponding application cbda
            for element in elements:
                if cls._is_composition_element(element):
                    flattened = cls._flatten_composition(element)
                    if flattened != element:
                        # Check if the flattened version exists in the same node
                        for other_element in elements:
                            if other_element == flattened:
                                return True
        
        return False
    
    @classmethod
    def _is_composition_element(cls, element):
        """Check if element has composition notation like (c∘b)da."""
        import re
        # Look for pattern: (anything containing ∘)element
        # This should handle nested parentheses like ((a∘b)∘c)d
        if '∘' in element and '(' in element and ')' in element:
            # Find the main parenthetical group at the start
            paren_count = 0
            composition_end = -1
            for i, char in enumerate(element):
                if char == '(':
                    paren_count += 1
                elif char == ')':
                    paren_count -= 1
                    if paren_count == 0:
                        composition_end = i
                        break
            
            # Check if we found a complete parenthetical group and there's content after it
            if composition_end > 0 and composition_end < len(element) - 1:
                composition_part = element[1:composition_end]  # Content inside first parentheses
                if '∘' in composition_part:
                    return True
        
        return False
    
    @classmethod
    def _flatten_composition(cls, element):
        """Convert (c∘b)da to cbda by flattening the composition."""
        import re
        
        # Find the main parenthetical composition at the start
        if not element.startswith('('):
            return element
            
        paren_count = 0
        composition_end = -1
        for i, char in enumerate(element):
            if char == '(':
                paren_count += 1
            elif char == ')':
                paren_count -= 1
                if paren_count == 0:
                    composition_end = i
                    break
        
        if composition_end == -1:
            return element
            
        composition = element[1:composition_end]  # Content inside parentheses
        remaining = element[composition_end + 1:]  # Content after parentheses
        
        # Recursively flatten nested compositions and remove all ∘ symbols and nested parentheses
        def flatten_recursive(comp_str):
            # Remove all parentheses and ∘ symbols
            result = comp_str.replace('∘', '').replace('(', '').replace(')', '')
            return result
        
        flattened_composition = flatten_recursive(composition)
        
        return f"{flattened_composition}{remaining}"
    
    @staticmethod
    def button_text(objects, arrows) -> str:
        """Get the text to display on the proof step button."""
        return "Composition to Application"
    
    def apply(self) -> None:
        """Convert composition notation to application notation."""
        if not self.node:
            return
        
        # Store original text for undo
        self.original_text = self.node.get_display_text()
        self.original_base_name = self.node.get_text()
        
        display_text = self.node.get_display_text()
        
        if ':' in display_text:
            elements_part, base_part = display_text.split(':', 1)
            elements = [elem.strip() for elem in elements_part.split(',') if elem.strip()]
            
            # Find composition-application pairs and convert them
            new_elements = []
            processed_elements = set()
            
            for element in elements:
                if element in processed_elements:
                    continue
                
                if self._is_composition_element(element):
                    flattened = self._flatten_composition(element)
                    
                    # Check if flattened version exists
                    if flattened in elements and flattened != element:
                        # Create equality statement and mark both as processed
                        equality = f"{element}={flattened}"
                        new_elements.append(equality)
                        processed_elements.add(element)
                        processed_elements.add(flattened)
                    else:
                        # No corresponding flattened version, keep as is
                        new_elements.append(element)
                        processed_elements.add(element)
                else:
                    # Check if this is a flattened version of some composition
                    found_composition = False
                    for other_element in elements:
                        if (other_element not in processed_elements and 
                            self._is_composition_element(other_element) and
                            self._flatten_composition(other_element) == element):
                            # This element is the flattened version of other_element
                            equality = f"{other_element}={element}"
                            new_elements.append(equality)
                            processed_elements.add(element)
                            processed_elements.add(other_element)
                            found_composition = True
                            break
                    
                    if not found_composition:
                        # No corresponding composition version, keep as is
                        new_elements.append(element)
                        processed_elements.add(element)
            
            # Reconstruct the display text
            new_elements_part = ", ".join(new_elements)
            new_display_text = f"{new_elements_part}:{base_part}"
            
            # Update the node
            self.node.set_text(new_display_text)
            self.node._base_name = self.original_base_name
            
            # Update connection points of all arrows connected to this node
            self._update_connected_arrows()
    
    def _update_connected_arrows(self):
        """Update connection points of all arrows connected to this node."""
        if not self.node or not self.node.scene():
            return
        
        # Find all arrows connected to this node
        for item in self.node.scene().items():
            if hasattr(item, 'get_source') and hasattr(item, 'get_target'):
                # Check if this arrow is connected to the node
                if item.get_source() == self.node or item.get_target() == self.node:
                    item.update_position()
        
        # Check and adjust grid spacing if auto-spacing is enabled
        self._check_auto_grid_spacing()
    
    def unapply(self) -> None:
        """Restore the original node text."""
        if not self.node:
            return
            
        # Restore original text and base name
        if hasattr(self, 'original_text'):
            self.node.set_text(self.original_text)
        if hasattr(self, 'original_base_name'):
            self.node._base_name = self.original_base_name

        # Update connection points of all arrows connected to this node
        self._update_connected_arrows()


class ApplicationToKernelIsZeroProofStep(ProofStep):
    """Proof step to mark applications to kernel as zero: g𝐤(g)a = 0."""
    
    def __init__(self, scene, selected_objects, selected_arrows):
        super().__init__(scene)
        self.node = selected_objects[0] if selected_objects else None
        self.selected_objects = selected_objects
        self.selected_arrows = selected_arrows
        self.original_text = None
        self.original_base_name = None
    
    @classmethod
    def get_name(cls) -> str:
        """Return the human-readable name of this proof step."""
        return "⚬ Application to Kernel is Zero"
    
    @classmethod
    def get_description(cls) -> str:
        """Return a description of what this proof step does."""
        return "⚬ Mark application to kernel as zero: g𝐤(g)a = 0"
    
    @classmethod
    def is_applicable(cls, objects, arrows, scene=None) -> bool:
        """Return True if exactly one object is selected and contains g𝐤(g) pattern."""
        if len(objects) != 1 or len(arrows) != 0:
            return False
        
        obj = objects[0]
        if not hasattr(obj, 'get_display_text'):
            return False
        
        display_text = obj.get_display_text()
        
        # Look for pattern g𝐤(g) where g can be any function name
        return cls._contains_kernel_application_pattern(display_text)
    
    @classmethod
    def _contains_kernel_application_pattern(cls, text):
        """Check if text contains pattern like g𝐤(g) where g matches."""
        import re
        
        # Pattern: any sequence (including Unicode Greek) followed by 𝐤( then same sequence then ) 
        # This matches patterns like: f𝐤(f), abc𝐤(abc), α𝐤(α), etc.
        pattern = r'([a-zA-Z\u0370-\u03FF\u1F00-\u1FFF]+)𝐤\(\1\)'
        
        return bool(re.search(pattern, text))
    
    @staticmethod
    def button_text(objects, arrows) -> str:
        """Get the text to display on the proof step button."""
        if len(objects) == 1:
            obj = objects[0]
            display_text = obj.get_display_text()
            
            # Find and extract the kernel application pattern
            import re
            pattern = r'([a-zA-Z\u0370-\u03FF\u1F00-\u1FFF]+)𝐤\(\1\)'
            match = re.search(pattern, display_text)
            if match:
                func_name = match.group(1)
                return f"Mark {func_name}𝐤({func_name}) = 0"
        
        return "Application to Kernel is Zero"
    
    def apply(self) -> None:
        """Mark kernel applications as zero."""
        if not self.node:
            return
        
        # Store original text for undo
        self.original_text = self.node.get_display_text()
        self.original_base_name = self.node.get_text()
        
        display_text = self.node.get_display_text()
        
        # Process the text to mark kernel applications as zero
        new_text = self._mark_kernel_applications_as_zero(display_text)
        
        if new_text != display_text:
            # Update the node with the new text
            self.node.set_text(new_text)
            
            # Preserve base name if it exists
            if ':' in new_text:
                base_name = new_text.split(':', 1)[1].strip()
                self.node._base_name = base_name
            
            # Update connection points
            self._update_connected_arrows()
    
    def _mark_kernel_applications_as_zero(self, text):
        """Transform text to mark kernel applications as zero."""
        import re
        
        if ':' in text:
            elements_part, base_part = text.split(':', 1)
        else:
            elements_part = text
            base_part = text
        
        # Find all kernel application patterns and mark them as zero
        # Pattern matches: f𝐤(f)α, g𝐤(g)xyz, etc. - now includes Unicode characters
        pattern = r'([a-zA-Z\u0370-\u03FF\u1F00-\u1FFF]+)𝐤\(\1\)([a-zA-Z\u0370-\u03FF\u1F00-\u1FFF]*)'
        
        def replace_with_zero(match):
            func_name = match.group(1)
            element_part = match.group(2)
            # Create the zero expression
            if element_part:
                return f"{func_name}𝐤({func_name}){element_part}=0"
            else:
                return f"{func_name}𝐤({func_name})=0"
        
        # Apply the transformation
        new_elements_part = re.sub(pattern, replace_with_zero, elements_part)
        
        # Reconstruct the full text
        if ':' in text:
            return f"{new_elements_part}:{base_part}"
        else:
            return new_elements_part
    
    def _update_connected_arrows(self):
        """Update connection points of all arrows connected to this node."""
        if not self.node or not self.node.scene():
            return
        
        # Find all arrows connected to this node
        for item in self.node.scene().items():
            if hasattr(item, 'get_source') and hasattr(item, 'get_target'):
                # Check if this arrow is connected to the node
                if item.get_source() == self.node or item.get_target() == self.node:
                    item.update_position()
        
        # Check and adjust grid spacing if auto-spacing is enabled
        self._check_auto_grid_spacing()
    
    def unapply(self) -> None:
        """Restore the original node text."""
        if not self.node:
            return
            
        # Restore original text and base name
        if hasattr(self, 'original_text'):
            self.node.set_text(self.original_text)
        if hasattr(self, 'original_base_name'):
            self.node._base_name = self.original_base_name

        # Update connection points of all arrows connected to this node
        self._update_connected_arrows()


class KernelDefinitionProofStep(ProofStep):
    """Proof step to move elements to kernel based on fx=0: if fx=0 then x ∈ Ker f."""
    
    def __init__(self, scene, selected_objects, selected_arrows):
        super().__init__(scene)
        self.node = selected_objects[0] if selected_objects else None
        self.selected_objects = selected_objects
        self.selected_arrows = selected_arrows
        self.original_text = None
        self.original_base_name = None
        self.kernel_node = None
        self.created_kernel_node = False
        self.function_name = None
        self.element_name = None
    
    @classmethod
    def get_name(cls) -> str:
        """Return the human-readable name of this proof step."""
        return "⚬ Apply Kernel Definition"
    
    @classmethod
    def get_description(cls) -> str:
        """Return a description of what this proof step does."""
        return "⚬ Move element to kernel: if fx=0 then x ∈ Ker f"
    
    @classmethod
    def is_applicable(cls, objects, arrows, scene=None) -> bool:
        """Return True if exactly one object contains fx=0 pattern."""
        if len(objects) != 1 or len(arrows) != 0:
            return False
        
        obj = objects[0]
        if not hasattr(obj, 'get_display_text'):
            return False
        
        display_text = obj.get_display_text()
        return cls._contains_kernel_definition_pattern(display_text)
    
    @classmethod
    def _contains_kernel_definition_pattern(cls, text):
        """Check if text contains pattern like fx=0 where f is function and x is element."""
        import re
        
        # Pattern: function_name + element + =0
        # Matches: fa=0, gα=0, hxyz=0, etc.
        pattern = r'([a-zA-Z\u0370-\u03FF\u1F00-\u1FFF]+)([a-zA-Z\u0370-\u03FF\u1F00-\u1FFF]+)=0'
        
        return bool(re.search(pattern, text))
    
    @classmethod
    def _extract_kernel_definition_info(cls, text):
        """Extract function name and element from fx=0 pattern."""
        import re
        
        pattern = r'([a-zA-Z\u0370-\u03FF\u1F00-\u1FFF]+)([a-zA-Z\u0370-\u03FF\u1F00-\u1FFF]+)=0'
        match = re.search(pattern, text)
        
        if match:
            # For now, assume first character is function, rest is element
            full_expr = match.group(0)[:-2]  # Remove =0
            if len(full_expr) >= 2:
                function_name = full_expr[0]  # First character as function
                element_name = full_expr[1:]   # Rest as element
                return function_name, element_name
        
        return None, None
    
    @staticmethod
    def button_text(objects, arrows) -> str:
        """Get the text to display on the proof step button."""
        if len(objects) == 1:
            obj = objects[0]
            display_text = obj.get_display_text()
            
            func, elem = KernelDefinitionProofStep._extract_kernel_definition_info(display_text)
            if func and elem:
                return f"Move {elem} to Ker {func}"
        
        return "Apply Kernel Definition"
    
    def apply(self) -> None:
        """Apply kernel definition: move element from fx=0 to Ker f."""
        if not self.node:
            return
        
        # Store original text for undo
        self.original_text = self.node.get_display_text()
        self.original_base_name = self.node.get_text()
        
        # Extract function and element from fx=0 pattern
        display_text = self.node.get_display_text()
        self.function_name, self.element_name = self._extract_kernel_definition_info(display_text)
        
        if not self.function_name or not self.element_name:
            return
        
        # Find or create kernel node
        kernel_node_name = f"Ker {self.function_name}"
        self.kernel_node = self._find_kernel_node(kernel_node_name)
        
        if not self.kernel_node:
            # Create kernel node if it doesn't exist
            self.kernel_node = self._create_kernel_node(kernel_node_name)
            self.created_kernel_node = True
        
        # Remove fx=0 from original node and add x to kernel node
        self._remove_zero_element_from_node()
        self._add_element_to_kernel_node()
        
        # Blink the kernel node blue to show what happened
        self._blink_node_blue(self.kernel_node)
    
    def _find_kernel_node(self, kernel_name):
        """Find existing kernel node in the scene."""
        if not self.scene:
            return None
        
        for item in self.scene.items():
            if (hasattr(item, 'get_text') and not hasattr(item, 'get_source') and 
                hasattr(item, 'get_display_text')):
                # This is a node, check if it's the kernel we want
                display_text = item.get_display_text()
                if ':' in display_text:
                    base_name = display_text.split(':', 1)[1].strip()
                else:
                    base_name = display_text.strip()
                
                if base_name == kernel_name:
                    return item
        
        return None
    
    def _create_kernel_node(self, kernel_name):
        """Create a new kernel node."""
        from widget.object_node import Object
        
        # Create kernel node
        kernel_node = Object(kernel_name)
        
        # Position it near the original node
        original_pos = self.node.pos()
        kernel_node.setPos(original_pos.x(), original_pos.y() + 150)  # Below original
        
        # Add to scene
        self.scene.addItem(kernel_node)
        
        return kernel_node
    
    def _remove_zero_element_from_node(self):
        """Remove the fx=0 element from the original node."""
        display_text = self.node.get_display_text()
        
        if ':' in display_text:
            elements_part, base_part = display_text.split(':', 1)
            elements = [elem.strip() for elem in elements_part.split(',') if elem.strip()]
            
            # Remove the fx=0 element
            zero_pattern = f"{self.function_name}{self.element_name}=0"
            elements = [elem for elem in elements if elem != zero_pattern]
            
            # Reconstruct the text
            if elements:
                new_text = f"{','.join(elements)}:{base_part}"
            else:
                new_text = base_part  # Only base name if no elements left
            
            self.node.set_text(new_text)
    
    def _add_element_to_kernel_node(self):
        """Add the element x to the Ker f node."""
        current_text = self.kernel_node.get_display_text()
        
        if ':' in current_text:
            # Kernel node already has elements
            elements_part, base_part = current_text.split(':', 1)
            existing_elements = [elem.strip() for elem in elements_part.split(',') if elem.strip()]
            
            # Add the new element if not already present
            if self.element_name not in existing_elements:
                existing_elements.append(self.element_name)
                new_text = f"{','.join(existing_elements)}:{base_part}"
            else:
                new_text = current_text  # Element already exists
        else:
            # Kernel node has no elements yet
            base_name = current_text.strip()
            new_text = f"{self.element_name}:{base_name}"
        
        self.kernel_node.set_text(new_text)
        
        # Preserve base name
        if ':' in new_text:
            base_name = new_text.split(':', 1)[1].strip()
            self.kernel_node._base_name = base_name
    
    def _blink_node_blue(self, node):
        """Make the node blink blue once to indicate the change."""
        from PyQt6.QtCore import QTimer
        from PyQt6.QtGui import QColor, QPen, QBrush
        
        if not node:
            return
        
        # Store original colors
        original_pen = node._pen if hasattr(node, '_pen') else None
        original_brush = node._brush if hasattr(node, '_brush') else None
        
        # Set blue highlighting
        blue_pen = QPen(QColor(0, 100, 255), 3)  # Blue border
        blue_brush = QBrush(QColor(173, 216, 230, 100))  # Light blue fill
        
        node._pen = blue_pen
        node._brush = blue_brush
        node.update()
        
        # Timer to restore original colors after 1 second
        def restore_colors():
            if original_pen:
                node._pen = original_pen
            if original_brush:
                node._brush = original_brush
            node.update()
        
        timer = QTimer()
        timer.timeout.connect(restore_colors)
        timer.setSingleShot(True)
        timer.start(1000)  # 1 second
    
    def unapply(self) -> None:
        """Undo the kernel definition application."""
        if not self.node:
            return
        
        # Restore original text and base name to the source node
        if hasattr(self, 'original_text'):
            self.node.set_text(self.original_text)
        if hasattr(self, 'original_base_name'):
            self.node._base_name = self.original_base_name
        
        # Remove element from kernel node or delete kernel node if we created it
        if self.kernel_node and self.element_name:
            if self.created_kernel_node:
                # We created the kernel node, so remove it entirely
                if self.kernel_node.scene():
                    self.kernel_node.scene().removeItem(self.kernel_node)
            else:
                # Remove just the element we added
                current_text = self.kernel_node.get_display_text()
                if ':' in current_text:
                    elements_part, base_part = current_text.split(':', 1)
                    elements = [elem.strip() for elem in elements_part.split(',') if elem.strip()]
                    
                    # Remove our element
                    elements = [elem for elem in elements if elem != self.element_name]
                    
                    # Reconstruct kernel node text
                    if elements:
                        new_kernel_text = f"{','.join(elements)}:{base_part}"
                    else:
                        new_kernel_text = base_part  # Only base name if no elements left
                    
                    self.kernel_node.set_text(new_kernel_text)


class CommutingPathsProofStep(ProofStep):
    """Proof step to equate commuting paths: if cba and fga start from same element a, create cba=fga."""
    
    def __init__(self, scene, selected_objects, selected_arrows):
        super().__init__(scene)
        self.node = selected_objects[0] if selected_objects else None
        self.selected_objects = selected_objects
        self.selected_arrows = selected_arrows
        self.original_text = None
        self.original_base_name = None
    
    @classmethod
    def get_name(cls) -> str:
        """Return the human-readable name of this proof step."""
        return "⚬ Equate Commuting Paths"
    
    @classmethod
    def get_description(cls) -> str:
        """Return a description of what this proof step does."""
        return "⚬ Create equality between different paths from same element"
    
    @classmethod
    def is_applicable(cls, objects, arrows, scene=None) -> bool:
        """Return True if exactly one object with multiple paths from same element."""
        if len(objects) != 1 or len(arrows) != 0:
            return False
        
        obj = objects[0]
        if not hasattr(obj, 'get_display_text'):
            return False
        
        display_text = obj.get_display_text()
        return cls._has_commuting_paths(display_text)
    
    @classmethod
    def _has_commuting_paths(cls, text):
        """Check if text has multiple composition/application paths from same element."""
        if ':' not in text:
            return False
        
        elements_part = text.split(':', 1)[0]
        elements = [elem.strip() for elem in elements_part.split(',') if elem.strip()]
        
        # Group elements by their suffix (the element they're applied to)
        suffix_groups = {}
        
        for element in elements:
            # Extract the suffix (last character if it looks like function application)
            suffix = cls._extract_element_suffix(element)
            if suffix:
                if suffix not in suffix_groups:
                    suffix_groups[suffix] = []
                suffix_groups[suffix].append(element)
        
        # Check if any suffix has multiple different paths
        for suffix, paths in suffix_groups.items():
            if len(paths) >= 2:
                # Check if the paths are actually different (different prefixes)
                prefixes = [cls._extract_path_prefix(path) for path in paths]
                unique_prefixes = set(prefix for prefix in prefixes if prefix)
                if len(unique_prefixes) >= 2:
                    return True
        
        return False
    
    @classmethod
    def _extract_element_suffix(cls, element):
        """Extract the element suffix from a path like 'cba' -> 'a'."""
        # Skip if it's an equality or has special characters
        if '=' in element or '(' in element or '∘' in element:
            return None
        
        # For simple alphanumeric strings, last char is the element
        if element and element[-1].islower() and element[-1].isalpha():
            return element[-1]
        
        return None
    
    @classmethod
    def _extract_path_prefix(cls, path):
        """Extract the function composition prefix from a path like 'cba' -> 'cb'."""
        suffix = cls._extract_element_suffix(path)
        if suffix and path.endswith(suffix):
            return path[:-1]  # Everything except the last character
        return None
    
    @staticmethod
    def button_text(objects, arrows) -> str:
        """Get the text to display on the proof step button."""
        if len(objects) == 1:
            obj = objects[0]
            display_text = obj.get_display_text()
            
            # Find commuting paths and show example
            if ':' in display_text:
                elements_part = display_text.split(':', 1)[0]
                elements = [elem.strip() for elem in elements_part.split(',') if elem.strip()]
                
                # Find first pair of commuting paths
                suffix_groups = {}
                for element in elements:
                    suffix = CommutingPathsProofStep._extract_element_suffix(element)
                    if suffix:
                        if suffix not in suffix_groups:
                            suffix_groups[suffix] = []
                        suffix_groups[suffix].append(element)
                
                for suffix, paths in suffix_groups.items():
                    if len(paths) >= 2:
                        return f"Equate paths to {suffix}: {paths[0]}={paths[1]}"
        
        return "Equate Commuting Paths"
    
    def apply(self) -> None:
        """Create equalities between commuting paths."""
        if not self.node:
            return
        
        # Store original text for undo
        self.original_text = self.node.get_display_text()
        self.original_base_name = self.node.get_text()
        
        display_text = self.node.get_display_text()
        new_text = self._create_path_equalities(display_text)
        
        if new_text != display_text:
            # Update the node with the new text
            self.node.set_text(new_text)
            
            # Preserve base name if it exists
            if ':' in new_text:
                base_name = new_text.split(':', 1)[1].strip()
                self.node._base_name = base_name
            
            # Update connection points
            self._update_connected_arrows()
    
    def _create_path_equalities(self, text):
        """Transform text to create equalities between commuting paths."""
        if ':' not in text:
            return text
        
        elements_part, base_part = text.split(':', 1)
        elements = [elem.strip() for elem in elements_part.split(',') if elem.strip()]
        
        # Group elements by their suffix
        suffix_groups = {}
        remaining_elements = []
        
        for element in elements:
            suffix = self._extract_element_suffix(element)
            if suffix:
                if suffix not in suffix_groups:
                    suffix_groups[suffix] = []
                suffix_groups[suffix].append(element)
            else:
                remaining_elements.append(element)
        
        # Create equalities for each suffix group
        new_elements = remaining_elements.copy()
        
        for suffix, paths in suffix_groups.items():
            if len(paths) >= 2:
                # Create equality: path1=path2=...
                equality = '='.join(paths)
                new_elements.append(equality)
            else:
                # Single path, keep as is
                new_elements.extend(paths)
        
        # Reconstruct the text
        new_elements_part = ','.join(new_elements)
        return f"{new_elements_part}:{base_part}"
    
    def _update_connected_arrows(self):
        """Update connection points of all arrows connected to this node."""
        if not self.node or not self.node.scene():
            return
        
        # Find all arrows connected to this node
        for item in self.node.scene().items():
            if hasattr(item, 'get_source') and hasattr(item, 'get_target'):
                # Check if this arrow is connected to the node
                if item.get_source() == self.node or item.get_target() == self.node:
                    item.update_position()
        
        # Check and adjust grid spacing if auto-spacing is enabled
        self._check_auto_grid_spacing()
    
    def unapply(self) -> None:
        """Restore the original node text."""
        if not self.node:
            return
            
        # Restore original text and base name
        if hasattr(self, 'original_text'):
            self.node.set_text(self.original_text)
        if hasattr(self, 'original_base_name'):
            self.node._base_name = self.original_base_name

        # Update connection points of all arrows connected to this node
        self._update_connected_arrows()


class CommutesProofStep(ProofStep):
    """Proof step to combine two composition paths into equality: f∘g∘...(a) = h∘i∘...(a)."""
    
    def __init__(self, scene, selected_objects, selected_arrows):
        super().__init__(scene)
        self.node = selected_objects[0] if selected_objects else None
        self.selected_objects = selected_objects
        self.selected_arrows = selected_arrows
        self.original_text = None
        self.original_base_name = None
        self.path1 = None
        self.path2 = None
        self.common_element = None
    
    @classmethod
    def get_name(cls) -> str:
        """Return the human-readable name of this proof step."""
        return "🔄 Commutes"
    
    @classmethod
    def get_description(cls) -> str:
        """Return a description of what this proof step does."""
        return "🔄 Combine two composition paths into equality"
    
    @classmethod
    def is_applicable(cls, objects, arrows, scene=None) -> bool:
        """Return True if exactly one object is selected with two composition paths to same element."""
        if len(objects) != 1 or len(arrows) != 0:
            return False
        
        node = objects[0]
        if not hasattr(node, 'get_display_text'):
            return False
        
        display_text = node.get_display_text()
        
        # Check for two elements that are compositions ending with the same base element
        if ':' in display_text:
            elements_part = display_text.split(':', 1)[0]
            elements = [elem.strip() for elem in elements_part.split(',') if elem.strip()]
            
            if len(elements) == 2:
                # Check if both elements are composition paths to the same base element
                path1_info = cls._parse_composition_path(elements[0])
                path2_info = cls._parse_composition_path(elements[1])
                
                if (path1_info and path2_info and 
                    path1_info['base_element'] == path2_info['base_element'] and
                    path1_info['base_element'] is not None):
                    return True
        
        return False
    
    @classmethod
    def _parse_composition_path(cls, element):
        """Parse a composition path to extract composition and base element."""
        # Handle patterns like "f(a)", "(g∘f)(a)", "(h∘g∘f)(a)"
        if '(' not in element or ')' not in element:
            return None
        
        # Find the base element (after the last opening parenthesis)
        last_paren = element.rfind('(')
        if last_paren == -1:
            return None
        
        base_element = element[last_paren+1:element.rfind(')')]
        composition_part = element[:last_paren]
        
        # Remove outer parentheses if present for multi-function composition
        if composition_part.startswith('(') and composition_part.endswith(')'):
            composition_part = composition_part[1:-1]
        
        return {
            'composition': composition_part,
            'base_element': base_element,
            'full_path': element
        }
    
    @staticmethod
    def button_text(objects, arrows) -> str:
        """Get the text to display on the proof step button."""
        if len(objects) == 1:
            node = objects[0]
            display_text = node.get_display_text()
            
            if ':' in display_text:
                elements_part = display_text.split(':', 1)[0]
                elements = [elem.strip() for elem in elements_part.split(',') if elem.strip()]
                
                if len(elements) == 2:
                    path1_info = CommutesProofStep._parse_composition_path(elements[0])
                    path2_info = CommutesProofStep._parse_composition_path(elements[1])
                    
                    if path1_info and path2_info:
                        base_elem = path1_info['base_element']
                        comp1 = path1_info['composition']
                        comp2 = path2_info['composition']
                        return f"Commutes so {comp1}({base_elem}) = {comp2}({base_elem})"
        
        return "Commutes"
    
    def apply(self) -> None:
        """Combine two composition paths into equality."""
        if not self.node:
            return
        
        # Store original text for undo
        self.original_text = self.node.get_display_text()
        self.original_base_name = self.node.get_text()
        
        display_text = self.node.get_display_text()
        
        if ':' in display_text:
            elements_part, base_part = display_text.split(':', 1)
            elements = [elem.strip() for elem in elements_part.split(',') if elem.strip()]
            
            if len(elements) == 2:
                path1_info = self._parse_composition_path(elements[0])
                path2_info = self._parse_composition_path(elements[1])
                
                if path1_info and path2_info and path1_info['base_element'] == path2_info['base_element']:
                    # Create equality statement
                    equality = f"{path1_info['full_path']}={path2_info['full_path']}"
                    new_display_text = f"{equality}:{base_part}"
                    
                    # Update the node
                    self.node.set_text(new_display_text)
                    self.node._base_name = self.original_base_name
                    
                    # Update connection points of all arrows connected to this node
                    self._update_connected_arrows()
    
    def _update_connected_arrows(self):
        """Update connection points of all arrows connected to this node."""
        if not self.node or not self.node.scene():
            return
        
        # Find all arrows connected to this node
        for item in self.node.scene().items():
            if hasattr(item, 'get_source') and hasattr(item, 'get_target'):
                # Check if this arrow is connected to the node
                if item.get_source() == self.node or item.get_target() == self.node:
                    item.update_position()
        
        # Check and adjust grid spacing if auto-spacing is enabled
        self._check_auto_grid_spacing()
    
    def unapply(self) -> None:
        """Restore the original node text."""
        if not self.node:
            return
            
        # Restore original text and base name
        if hasattr(self, 'original_text'):
            self.node.set_text(self.original_text)
        if hasattr(self, 'original_base_name'):
            self.node._base_name = self.original_base_name
 
 
 c l a s s   S i m p l i f y I n c l u s i o n P r o o f S t e p ( P r o o f S t e p ) : 
         " " " P r o o f   s t e p   t o   s i m p l i f y   i n c l u s i o n   a p p l i c a t i o n s :   f a : X   �!  a : X   w h e n   f   i s   a n   i n c l u s i o n . " " " 
         
         d e f   _ _ i n i t _ _ ( s e l f ,   s c e n e ,   s e l e c t e d _ o b j e c t s ,   s e l e c t e d _ a r r o w s ) : 
                 s u p e r ( ) . _ _ i n i t _ _ ( s c e n e ) 
                 s e l f . n o d e   =   s e l e c t e d _ o b j e c t s [ 0 ]   i f   s e l e c t e d _ o b j e c t s   e l s e   N o n e 
                 s e l f . s e l e c t e d _ o b j e c t s   =   s e l e c t e d _ o b j e c t s 
                 s e l f . s e l e c t e d _ a r r o w s   =   s e l e c t e d _ a r r o w s 
                 s e l f . o r i g i n a l _ t e x t   =   N o n e 
                 s e l f . o r i g i n a l _ b a s e _ n a m e   =   N o n e 
                 s e l f . i n c l u s i o n s _ f o u n d   =   [ ] 
         
         @ c l a s s m e t h o d 
         d e f   g e t _ n a m e ( c l s )   - >   s t r : 
                 " " " R e t u r n   t h e   h u m a n - r e a d a b l e   n a m e   o f   t h i s   p r o o f   s t e p . " " " 
                 r e t u r n   " �!  S i m p l i f y   I n c l u s i o n " 
         
         @ c l a s s m e t h o d 
         d e f   g e t _ d e s c r i p t i o n ( c l s )   - >   s t r : 
                 " " " R e t u r n   a   d e s c r i p t i o n   o f   w h a t   t h i s   p r o o f   s t e p   d o e s . " " " 
                 r e t u r n   " �!  R e m o v e   i n c l u s i o n   f u n c t i o n   f r o m   e l e m e n t s :   f a : X   �!  a : X " 
         
         @ c l a s s m e t h o d 
         d e f   i s _ a p p l i c a b l e ( c l s ,   o b j e c t s ,   a r r o w s ,   s c e n e = N o n e )   - >   b o o l : 
                 " " " R e t u r n   T r u e   i f   e x a c t l y   o n e   o b j e c t   i s   s e l e c t e d   t h a t   c o n t a i n s   i n c l u s i o n   a p p l i c a t i o n s . " " " 
                 i f   l e n ( o b j e c t s )   ! =   1   o r   l e n ( a r r o w s )   ! =   0 : 
                         r e t u r n   F a l s e 
                 
                 n o d e   =   o b j e c t s [ 0 ] 
                 i f   n o t   h a s a t t r ( n o d e ,   " g e t _ d i s p l a y _ t e x t " )   o r   n o t   s c e n e : 
                         r e t u r n   F a l s e 
                 
                 d i s p l a y _ t e x t   =   n o d e . g e t _ d i s p l a y _ t e x t ( ) 
                 
                 #   F i n d   a l l   a r r o w s   i n   t h e   s c e n e   t o   c h e c k   f o r   i n c l u s i o n s 
                 a r r o w s _ i n _ s c e n e   =   [ i t e m   f o r   i t e m   i n   s c e n e . i t e m s ( )   
                                                     i f   h a s a t t r ( i t e m ,   " g e t _ s o u r c e " )   a n d   h a s a t t r ( i t e m ,   " g e t _ t a r g e t " )   
                                                     a n d   h a s a t t r ( i t e m ,   " _ i s _ i n c l u s i o n " ) ] 
                 
                 #   G e t   i n c l u s i o n   f u n c t i o n   n a m e s 
                 i n c l u s i o n _ f u n c t i o n s   =   [ ] 
                 f o r   a r r o w   i n   a r r o w s _ i n _ s c e n e : 
                         i f   a r r o w . _ i s _ i n c l u s i o n   a n d   h a s a t t r ( a r r o w ,   " g e t _ t e x t " ) : 
                                 a r r o w _ t e x t   =   a r r o w . g e t _ t e x t ( ) . s t r i p ( ) 
                                 i f   a r r o w _ t e x t :     #   N o n - e m p t y   a r r o w   l a b e l 
                                         i n c l u s i o n _ f u n c t i o n s . a p p e n d ( a r r o w _ t e x t ) 
                 
                 i f   n o t   i n c l u s i o n _ f u n c t i o n s : 
                         r e t u r n   F a l s e 
                 
                 #   C h e c k   i f   t h e   n o d e ' s   t e x t   c o n t a i n s   a n y   p a t t e r n s   l i k e   " f a : X "   w h e r e   f   i s   a n   i n c l u s i o n 
                 r e t u r n   c l s . _ c o n t a i n s _ i n c l u s i o n _ a p p l i c a t i o n s ( d i s p l a y _ t e x t ,   i n c l u s i o n _ f u n c t i o n s ) 
         
         @ c l a s s m e t h o d 
         d e f   _ c o n t a i n s _ i n c l u s i o n _ a p p l i c a t i o n s ( c l s ,   t e x t ,   i n c l u s i o n _ f u n c t i o n s ) : 
                 " " " C h e c k   i f   t e x t   c o n t a i n s   p a t t e r n s   l i k e   ' f a : X '   w h e r e   f   i s   a n   i n c l u s i o n   f u n c t i o n . " " " 
                 i m p o r t   r e 
                 
                 f o r   f u n c _ n a m e   i n   i n c l u s i o n _ f u n c t i o n s : 
                         #   E s c a p e   f u n c t i o n   n a m e   f o r   r e g e x 
                         e s c a p e d _ f u n c   =   r e . e s c a p e ( f u n c _ n a m e ) 
                         
                         #   P a t t e r n :   f u n c t i o n   n a m e   f o l l o w e d   b y   e l e m e n t ( s )   f o l l o w e d   b y   c o l o n 
                         #   T h i s   c a p t u r e s   p a t t e r n s   l i k e   " f a : " ,   " f ��: " ,   " f 1 2 3 : " ,   e t c . 
                         p a t t e r n   =   r f " { e s c a p e d _ f u n c } ( [ a - z A - Z �- ��- �\ u 0 3 7 0 - \ u 0 3 F F \ u 1 F 0 0 - \ u 1 F F F 0 - 9 ] + ) : " 
                         
                         i f   r e . s e a r c h ( p a t t e r n ,   t e x t ) : 
                                 r e t u r n   T r u e 
                 
                 r e t u r n   F a l s e 
         
         @ c l a s s m e t h o d 
         d e f   _ f i n d _ i n c l u s i o n _ a p p l i c a t i o n s ( c l s ,   t e x t ,   i n c l u s i o n _ f u n c t i o n s ) : 
                 " " " F i n d   a l l   i n c l u s i o n   a p p l i c a t i o n s   i n   t h e   t e x t   a n d   r e t u r n   r e p l a c e m e n t   i n f o . " " " 
                 i m p o r t   r e 
                 
                 a p p l i c a t i o n s   =   [ ] 
                 
                 f o r   f u n c _ n a m e   i n   i n c l u s i o n _ f u n c t i o n s : 
                         #   E s c a p e   f u n c t i o n   n a m e   f o r   r e g e x 
                         e s c a p e d _ f u n c   =   r e . e s c a p e ( f u n c _ n a m e ) 
                         
                         #   P a t t e r n :   f u n c t i o n   n a m e   f o l l o w e d   b y   e l e m e n t ( s )   f o l l o w e d   b y   c o l o n 
                         p a t t e r n   =   r f " { e s c a p e d _ f u n c } ( [ a - z A - Z �- ��- �\ u 0 3 7 0 - \ u 0 3 F F \ u 1 F 0 0 - \ u 1 F F F 0 - 9 ] + ) : " 
                         
                         f o r   m a t c h   i n   r e . f i n d i t e r ( p a t t e r n ,   t e x t ) : 
                                 f u l l _ m a t c h   =   m a t c h . g r o u p ( 0 )     #   e . g . ,   " f a : " 
                                 e l e m e n t   =   m a t c h . g r o u p ( 1 )           #   e . g . ,   " a " 
                                 r e p l a c e m e n t   =   f " { e l e m e n t } : "     #   e . g . ,   " a : " 
                                 
                                 a p p l i c a t i o n s . a p p e n d ( { 
                                         " o r i g i n a l " :   f u l l _ m a t c h , 
                                         " r e p l a c e m e n t " :   r e p l a c e m e n t , 
                                         " f u n c t i o n " :   f u n c _ n a m e , 
                                         " e l e m e n t " :   e l e m e n t , 
                                         " s t a r t " :   m a t c h . s t a r t ( ) , 
                                         " e n d " :   m a t c h . e n d ( ) 
                                 } ) 
                 
                 r e t u r n   a p p l i c a t i o n s 
         
         @ s t a t i c m e t h o d 
         d e f   b u t t o n _ t e x t ( o b j e c t s ,   a r r o w s )   - >   s t r : 
                 " " " G e t   t h e   t e x t   t o   d i s p l a y   o n   t h e   p r o o f   s t e p   b u t t o n . " " " 
                 i f   l e n ( o b j e c t s )   = =   1 : 
                         n o d e   =   o b j e c t s [ 0 ] 
                         i f   h a s a t t r ( n o d e ,   " s c e n e " )   a n d   n o d e . s c e n e ( ) : 
                                 s c e n e   =   n o d e . s c e n e ( ) 
                                 d i s p l a y _ t e x t   =   n o d e . g e t _ d i s p l a y _ t e x t ( ) 
                                 
                                 #   F i n d   i n c l u s i o n   f u n c t i o n s 
                                 a r r o w s _ i n _ s c e n e   =   [ i t e m   f o r   i t e m   i n   s c e n e . i t e m s ( )   
                                                                     i f   h a s a t t r ( i t e m ,   " g e t _ s o u r c e " )   a n d   h a s a t t r ( i t e m ,   " g e t _ t a r g e t " )   
                                                                     a n d   h a s a t t r ( i t e m ,   " _ i s _ i n c l u s i o n " ) ] 
                                 
                                 i n c l u s i o n _ f u n c t i o n s   =   [ ] 
                                 f o r   a r r o w   i n   a r r o w s _ i n _ s c e n e : 
                                         i f   a r r o w . _ i s _ i n c l u s i o n   a n d   h a s a t t r ( a r r o w ,   " g e t _ t e x t " ) : 
                                                 a r r o w _ t e x t   =   a r r o w . g e t _ t e x t ( ) . s t r i p ( ) 
                                                 i f   a r r o w _ t e x t : 
                                                         i n c l u s i o n _ f u n c t i o n s . a p p e n d ( a r r o w _ t e x t ) 
                                 
                                 #   F i n d   a p p l i c a t i o n s   t o   s h o w   i n   b u t t o n 
                                 a p p l i c a t i o n s   =   S i m p l i f y I n c l u s i o n P r o o f S t e p . _ f i n d _ i n c l u s i o n _ a p p l i c a t i o n s ( d i s p l a y _ t e x t ,   i n c l u s i o n _ f u n c t i o n s ) 
                                 
                                 i f   a p p l i c a t i o n s : 
                                         i f   l e n ( a p p l i c a t i o n s )   = =   1 : 
                                                 a p p   =   a p p l i c a t i o n s [ 0 ] 
                                                 r e t u r n   f " R e m o v e   i n c l u s i o n   { a p p [ \ " f u n c t i o n \ " ] } :   { a p p [ \ " f u n c t i o n \ " ] } { a p p [ \ " e l e m e n t \ " ] }   �!  { a p p [ \ " e l e m e n t \ " ] } " 
                                         e l s e : 
                                                 r e t u r n   f " S i m p l i f y   { l e n ( a p p l i c a t i o n s ) }   i n c l u s i o n s " 
                 
                 r e t u r n   " S i m p l i f y   I n c l u s i o n " 
         
         d e f   a p p l y ( s e l f )   - >   N o n e : 
                 " " " R e m o v e   i n c l u s i o n   f u n c t i o n s   f r o m   e l e m e n t s . " " " 
                 i f   n o t   s e l f . n o d e   o r   n o t   s e l f . n o d e . s c e n e ( ) : 
                         r e t u r n 
                 
                 #   S t o r e   o r i g i n a l   t e x t   f o r   u n d o 
                 s e l f . o r i g i n a l _ t e x t   =   s e l f . n o d e . g e t _ d i s p l a y _ t e x t ( ) 
                 s e l f . o r i g i n a l _ b a s e _ n a m e   =   s e l f . n o d e . g e t _ t e x t ( ) 
                 
                 s c e n e   =   s e l f . n o d e . s c e n e ( ) 
                 d i s p l a y _ t e x t   =   s e l f . n o d e . g e t _ d i s p l a y _ t e x t ( ) 
                 
                 #   F i n d   i n c l u s i o n   f u n c t i o n s 
                 a r r o w s _ i n _ s c e n e   =   [ i t e m   f o r   i t e m   i n   s c e n e . i t e m s ( )   
                                                     i f   h a s a t t r ( i t e m ,   " g e t _ s o u r c e " )   a n d   h a s a t t r ( i t e m ,   " g e t _ t a r g e t " )   
                                                     a n d   h a s a t t r ( i t e m ,   " _ i s _ i n c l u s i o n " ) ] 
                 
                 i n c l u s i o n _ f u n c t i o n s   =   [ ] 
                 f o r   a r r o w   i n   a r r o w s _ i n _ s c e n e : 
                         i f   a r r o w . _ i s _ i n c l u s i o n   a n d   h a s a t t r ( a r r o w ,   " g e t _ t e x t " ) : 
                                 a r r o w _ t e x t   =   a r r o w . g e t _ t e x t ( ) . s t r i p ( ) 
                                 i f   a r r o w _ t e x t : 
                                         i n c l u s i o n _ f u n c t i o n s . a p p e n d ( a r r o w _ t e x t ) 
                 
                 #   F i n d   a n d   r e p l a c e   a l l   i n c l u s i o n   a p p l i c a t i o n s 
                 n e w _ t e x t   =   d i s p l a y _ t e x t 
                 a p p l i c a t i o n s   =   s e l f . _ f i n d _ i n c l u s i o n _ a p p l i c a t i o n s ( d i s p l a y _ t e x t ,   i n c l u s i o n _ f u n c t i o n s ) 
                 
                 #   S o r t   b y   p o s i t i o n   ( r e v e r s e   o r d e r   t o   a v o i d   o f f s e t   i s s u e s ) 
                 a p p l i c a t i o n s . s o r t ( k e y = l a m b d a   x :   x [ " s t a r t " ] ,   r e v e r s e = T r u e ) 
                 
                 #   S t o r e   f o r   u n d o 
                 s e l f . i n c l u s i o n s _ f o u n d   =   a p p l i c a t i o n s 
                 
                 #   R e p l a c e   e a c h   a p p l i c a t i o n 
                 f o r   a p p   i n   a p p l i c a t i o n s : 
                         n e w _ t e x t   =   n e w _ t e x t [ : a p p [ " s t a r t " ] ]   +   a p p [ " r e p l a c e m e n t " ]   +   n e w _ t e x t [ a p p [ " e n d " ] : ] 
                 
                 #   U p d a t e   t h e   n o d e 
                 s e l f . n o d e . s e t _ t e x t ( n e w _ t e x t ) 
                 s e l f . n o d e . _ b a s e _ n a m e   =   s e l f . o r i g i n a l _ b a s e _ n a m e 
                 
                 #   U p d a t e   c o n n e c t i o n   p o i n t s   o f   a l l   a r r o w s   c o n n e c t e d   t o   t h i s   n o d e 
                 s e l f . _ u p d a t e _ c o n n e c t e d _ a r r o w s ( ) 
         
         d e f   _ u p d a t e _ c o n n e c t e d _ a r r o w s ( s e l f ) : 
                 " " " U p d a t e   c o n n e c t i o n   p o i n t s   o f   a l l   a r r o w s   c o n n e c t e d   t o   t h i s   n o d e . " " " 
                 i f   n o t   s e l f . n o d e   o r   n o t   s e l f . n o d e . s c e n e ( ) : 
                         r e t u r n 
                 
                 #   F i n d   a l l   a r r o w s   c o n n e c t e d   t o   t h i s   n o d e 
                 f o r   i t e m   i n   s e l f . n o d e . s c e n e ( ) . i t e m s ( ) : 
                         i f   h a s a t t r ( i t e m ,   " g e t _ s o u r c e " )   a n d   h a s a t t r ( i t e m ,   " g e t _ t a r g e t " ) : 
                                 #   C h e c k   i f   t h i s   a r r o w   i s   c o n n e c t e d   t o   t h e   n o d e 
                                 i f   i t e m . g e t _ s o u r c e ( )   = =   s e l f . n o d e   o r   i t e m . g e t _ t a r g e t ( )   = =   s e l f . n o d e : 
                                         i t e m . u p d a t e _ p o s i t i o n ( ) 
                 
                 #   C h e c k   a n d   a d j u s t   g r i d   s p a c i n g   i f   a u t o - s p a c i n g   i s   e n a b l e d 
                 s e l f . _ c h e c k _ a u t o _ g r i d _ s p a c i n g ( ) 
         
         d e f   u n a p p l y ( s e l f )   - >   N o n e : 
                 " " " R e s t o r e   t h e   o r i g i n a l   n o d e   t e x t . " " " 
                 i f   n o t   s e l f . n o d e : 
                         r e t u r n 
                         
                 #   R e s t o r e   o r i g i n a l   t e x t   a n d   b a s e   n a m e 
                 i f   h a s a t t r ( s e l f ,   " o r i g i n a l _ t e x t " ) : 
                         s e l f . n o d e . s e t _ t e x t ( s e l f . o r i g i n a l _ t e x t ) 
                 i f   h a s a t t r ( s e l f ,   " o r i g i n a l _ b a s e _ n a m e " ) : 
                         s e l f . n o d e . _ b a s e _ n a m e   =   s e l f . o r i g i n a l _ b a s e _ n a m e 
 
                 #   U p d a t e   c o n n e c t i o n   p o i n t s   o f   a l l   a r r o w s   c o n n e c t e d   t o   t h i s   n o d e 
                 s e l f . _ u p d a t e _ c o n n e c t e d _ a r r o w s ( ) 
  
 