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
        return f"Identity on {obj_name}"
    
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
            return f"1{subscript_text}"
        elif len(text) == 1:
            return f"1_{text}"
        else:
            return f"1_{{{text}}}"
    
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
        return "Compose Arrows"
    
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
        if '1_' not in text:
            return False
        
        # But must NOT be a pure identity morphism (like "1_X")
        import re
        if re.match(r'^1_[^∘]+$', text.strip()):
            return False  # Pure identity, nothing to cancel
        
        return True  # Has identities in composition, can cancel them
    
    @staticmethod
    def button_text(objects: List[Any], arrows: List[Any]) -> str:
        """Return the text for the proof step button."""
        return "Cancel Identities"
    
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
            "f∘g∘1_A∘h" -> "f∘g∘h"
            "1_X∘f∘g" -> "f∘g"  
            "f∘g∘1_Y" -> "f∘g"
            "f∘1_A∘g∘h" -> "f∘g∘h"
            "1_X" -> "1_X" (no change - pure identity)
        """
        import re
        
        # Check if this is a pure identity morphism (just "1_X" with no composition)
        if re.match(r'^1_[^∘]+$', text.strip()):
            # This is a pure identity morphism, don't cancel it
            return text
        
        # Pattern to match identity morphism with composition symbols
        # This matches: ∘1_<anything>∘ OR ∘1_<anything> OR 1_<anything>∘
        pattern = r'(∘1_[^∘]+∘|∘1_[^∘]+$|^1_[^∘]+∘)'
        
        # Keep removing until no more identities found
        while True:
            original = text
            
            # Remove identity with composition symbols on both sides: ∘1_X∘ -> ∘
            text = re.sub(r'∘1_[^∘]+∘', '∘', text)
            
            # Remove identity at the beginning with composition: 1_X∘ -> (empty)
            text = re.sub(r'^1_[^∘]+∘', '', text)
            
            # Remove identity at the end with composition: ∘1_X -> (empty)  
            text = re.sub(r'∘1_[^∘]+$', '', text)
            
            # Remove standalone identity: 1_X -> (empty)
            text = re.sub(r'^1_[^∘]+$', '', text)
            
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
            return f"Take Ker({arrow_text})"
        return "Take Kernel"
    
    def apply(self) -> None:
        """Create kernel object and morphism."""
        if not self.arrow:
            return
        
        # Get the source node of the original arrow
        source_node = self.arrow._start_node
        
        # Create kernel object name (𝒦𝑒𝓇 f) - full mathematical script
        arrow_text = self.arrow.get_text()
        kernel_name = f"𝒦ℯ𝓇 {arrow_text}"
        
        # Position the kernel object to the left of the source
        source_pos = source_node.pos()
        kernel_pos = QPointF(source_pos.x() - 150, source_pos.y())
        
        # Check if position is occupied and find nearest free position
        if hasattr(self.scene, '_is_grid_position_occupied'):
            kernel_pos = self.scene.snap_to_grid(kernel_pos)
            if self.scene._is_grid_position_occupied(kernel_pos):
                kernel_pos = self.scene._find_nearest_free_grid_position(kernel_pos)
        
        # Create kernel object
        from widget.object_node import Object
        self.kernel_object = Object(kernel_name)
        self.kernel_object.setPos(kernel_pos)
        self.scene.addItem(self.kernel_object)
        
        # Create kernel arrow k_f : Ker f -> A
        from widget.arrow import Arrow
        kernel_arrow_name = f"k_{arrow_text}"
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
        return "Take Element"
    
    @classmethod
    def get_description(cls) -> str:
        """Return a description of what this proof step does."""
        return "Take an element from an object"
    
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
        else:
            # Dialog was cancelled
            raise Exception("Element dialog cancelled")
    
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
        return "Map Element"
    
    @classmethod
    def get_description(cls) -> str:
        """Return a description of what this proof step does."""
        return "Map an element from domain to codomain via a function"
    
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
            # Get the codomain's base name (e.g., "B")
            codomain_base_name = codomain_node.get_text()  # This returns base_name
            
            # Handle composition notation properly
            mapped_element = self._create_mapped_element_notation(self.element_name, self.function_name)
            
            # Set the codomain to show "f(x):B" or "(g∘f)(x):B" format
            new_display_text = f"{mapped_element}:{codomain_base_name}"
            
            # Update the codomain node display text while preserving base name
            codomain_node.set_text(new_display_text)
            codomain_node._base_name = codomain_base_name
    
    def _create_mapped_element_notation(self, element_name, function_name):
        """Create proper function composition notation for mapped elements."""
        # Handle zero elements specially
        if '=0' in element_name:
            # For zero elements like "(e∘k_e)(a)=0", map to "f(0)=0"
            return f"{function_name}(0)=0"
        
        # Check if the element is already a function application
        if '(' in element_name and ')' in element_name:
            # Extract the existing composition and base element
            # e.g., "f(a)" -> composition="f", base_element="a"
            # e.g., "(g∘f)(a)" -> composition="g∘f", base_element="a"
            
            # Find the base element (after the last opening parenthesis)
            last_paren = element_name.rfind('(')
            if last_paren != -1:
                base_element = element_name[last_paren+1:element_name.rfind(')')]
                
                # Extract the existing function composition
                existing_composition = element_name[:last_paren]
                
                # If it's already in composition form like "(g∘f)", add to it
                if existing_composition.startswith('(') and existing_composition.endswith(')'):
                    # Remove outer parentheses and add new function
                    inner_composition = existing_composition[1:-1]
                    new_composition = f"({function_name}∘{inner_composition})"
                else:
                    # Simple function like "f", convert to composition
                    new_composition = f"({function_name}∘{existing_composition})"
                
                return f"{new_composition}({base_element})"
        
        # Simple element name, just apply the function
        return f"{function_name}({element_name})"
    
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
    """Proof step to mark kernel elements as zero: (e∘k_e)(a) = 0."""
    
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
        return "Kernel at Element is 0"
    
    @classmethod
    def get_description(cls) -> str:
        """Return a description of what this proof step does."""
        return "Mark kernel element as zero: (e∘k_e)(a) = 0"
    
    @classmethod
    def is_applicable(cls, objects, arrows, scene=None) -> bool:
        """Return True if exactly one object is selected and contains kernel element pattern."""
        if len(objects) != 1 or len(arrows) != 0:
            return False
        
        node = objects[0]
        if not hasattr(node, 'get_display_text'):
            return False
        
        display_text = node.get_display_text()
        
        # Check for pattern like "(e∘k_e)(a)" where element contains kernel composition
        # Look for elements that have the pattern (e∘k_e)(something)
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
        """Check if element matches kernel pattern (e∘k_e)(a)."""
        # Look for pattern containing ∘k_ which indicates kernel composition
        if '∘k_' in element and '(' in element and ')' in element:
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
                    # Transform (e∘k_e)(a) to (e∘k_e)(a)=0
                    transformed_elements.append(f"{element}=0")
                else:
                    transformed_elements.append(element)
            
            # Reconstruct the display text
            new_elements_part = ", ".join(transformed_elements)
            new_display_text = f"{new_elements_part}:{base_part}"
            
            # Update the node
            self.node.set_text(new_display_text)
            self.node._base_name = self.original_base_name
    
    def unapply(self) -> None:
        """Restore the original node text."""
        if not self.node:
            return
            
        # Restore original text and base name
        if hasattr(self, 'original_text'):
            self.node.set_text(self.original_text)
        if hasattr(self, 'original_base_name'):
            self.node._base_name = self.original_base_name