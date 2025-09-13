"""
Transparent button panel overlay for displaying proof step buttons.
"""
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QPushButton, 
                             QGraphicsProxyWidget, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPalette, QMouseEvent
from typing import List, Type
from core.proof_step import ProofStep
from core.undo_commands import ProofStepCommand


class ProofStepButton(QPushButton):
    """Custom button for proof steps with enhanced styling."""
    
    def __init__(self, proof_step_class: Type[ProofStep], scene, objects, arrows, parent=None):
        button_text = proof_step_class.button_text(objects, arrows)
        super().__init__(button_text, parent)
        
        self.proof_step_class = proof_step_class
        self.scene = scene
        self.objects = objects.copy()  # Make a copy to avoid reference issues
        self.arrows = arrows.copy()
        
        # Style the button
        self.setStyleSheet("""
            QPushButton {
                background-color: rgba(200, 220, 255, 180);
                border: 2px solid rgba(100, 150, 200, 200);
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: bold;
                color: rgba(50, 50, 50, 255);
            }
            QPushButton:hover {
                background-color: rgba(220, 240, 255, 220);
                border: 2px solid rgba(120, 170, 220, 240);
            }
            QPushButton:pressed {
                background-color: rgba(180, 200, 235, 240);
                border: 2px solid rgba(80, 130, 180, 240);
            }
        """)
        
        # Connect click to execute proof step
        self.clicked.connect(self.execute_proof_step)
    
    def execute_proof_step(self):
        """Execute the proof step when button is clicked."""
        # Find the button panel and emit the signal
        panel = self.parent()
        while panel and not hasattr(panel, 'proof_step_triggered'):
            panel = panel.parent()
        
        if panel and hasattr(panel, 'proof_step_triggered'):
            panel.proof_step_triggered.emit(self.proof_step_class)


class ProofStepButtonPanel(QFrame):
    """Transparent panel containing proof step buttons."""
    
    # Signal emitted when a proof step should be executed
    proof_step_triggered = pyqtSignal(type)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Set up transparent background
        self.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 120);
                border: 1px solid rgba(200, 200, 200, 180);
                border-radius: 12px;
            }
        """)
        
        # Set up layout
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(10, 8, 10, 8)
        self.layout.setSpacing(8)
        
        # Store reference to current buttons
        self.current_buttons = []
    
    def update_buttons(self, scene, objects, arrows, available_proof_steps):
        """Update the buttons based on current selection."""
        # Clear existing buttons
        self.clear_buttons()
        
        # Add new buttons for applicable proof steps
        for proof_step_class in available_proof_steps:
            if proof_step_class.is_applicable(objects, arrows):
                button = ProofStepButton(proof_step_class, scene, objects, arrows, self)
                self.layout.addWidget(button)
                self.current_buttons.append(button)
        
        # Show/hide panel based on whether there are buttons
        self.setVisible(len(self.current_buttons) > 0)
    
    def clear_buttons(self):
        """Remove all buttons from the panel."""
        for button in self.current_buttons:
            self.layout.removeWidget(button)
            button.deleteLater()
        self.current_buttons.clear()


class ProofStepOverlay(QWidget):
    """Overlay widget that sits on top of the diagram view."""
    
    def __init__(self, diagram_view, parent=None):
        super().__init__(parent)
        self.diagram_view = diagram_view
        self.main_window = self._find_main_window()
        
        # Don't set transparent for mouse events - we'll handle them manually
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.setStyleSheet("background-color: rgba(0, 0, 0, 0);")
        
        # Position the overlay at top-left of parent (the view)
        self.move(0, 0)
        
        # Set up layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Add button panel
        self.button_panel = ProofStepButtonPanel(self)
        layout.addWidget(self.button_panel, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        layout.addStretch()
        
        # Connect button panel signal
        self.button_panel.proof_step_triggered.connect(self.execute_proof_step)
        
        # Register available proof step classes
        self.proof_step_classes = self._get_available_proof_step_classes()
        
        # Initially hidden
        self.hide()
    
    def _find_main_window(self):
        """Find the main window in the parent hierarchy."""
        current = self.diagram_view
        while current is not None:
            # Import here to avoid circular imports
            from .main_window import MainWindow
            if isinstance(current, MainWindow):
                return current
            current = current.parent()
        return None
    
    def _get_available_proof_step_classes(self):
        """Get list of available proof step classes."""
        from core.proof_step import IdentityProofStep, CompositionProofStep, CancelIdentityProofStep, TakeKernelProofStep, TakeElementProofStep, MapElementProofStep, KernelAtElementIsZeroProofStep
        
        # Base proof steps
        proof_steps = [IdentityProofStep, CompositionProofStep, CancelIdentityProofStep]
        
        # Add abelian category specific proof steps
        if self.diagram_view.scene() and self.diagram_view.scene().is_abelian_category:
            proof_steps.append(TakeKernelProofStep)
            proof_steps.append(KernelAtElementIsZeroProofStep)  # Available in abelian categories
        
        # Add concrete category specific proof steps
        if self.diagram_view.scene() and self.diagram_view.scene().is_concrete_category:
            proof_steps.append(TakeElementProofStep)
            proof_steps.append(MapElementProofStep)
            proof_steps.append(KernelAtElementIsZeroProofStep)  # Also available in concrete categories
        
        return proof_steps
    
    def update_for_selection(self, selected_objects, selected_arrows):
        """Update the overlay based on current selection."""
        scene = self.diagram_view.scene()
        
        if not selected_objects and not selected_arrows:
            # Nothing selected, hide overlay
            self.hide()
            return
        
        # Update buttons
        self.button_panel.update_buttons(scene, selected_objects, selected_arrows, 
                                       self.proof_step_classes)
        
        # Show overlay if there are applicable proof steps
        if self.button_panel.current_buttons:
            # Make sure we cover the full view for proper mouse pass-through
            self._resize_to_match_view()
            self.show()
        else:
            self.hide()
    
    def _resize_to_match_view(self):
        """Resize overlay to match the diagram view size for proper mouse pass-through."""
        if self.diagram_view:
            # Make sure the overlay covers the entire view area
            self.resize(self.diagram_view.size())
            # Position at top-left of the view (0, 0) since it's a child widget
            self.move(0, 0)
    
    def resizeEvent(self, event):
        """Handle overlay resize events - match view size when shown."""
        super().resizeEvent(event)
        # The overlay needs to match the view size for proper mouse pass-through
        if self.isVisible() and self.diagram_view:
            self.resize(self.diagram_view.size())
    
    def execute_proof_step(self, proof_step_class):
        """Execute a proof step using the main window's undo system."""
        if not self.main_window:
            print("Warning: No main window found, cannot execute proof step")
            return
        
        scene = self.diagram_view.scene()
        if not scene:
            return
        
        selected_objects = []
        selected_arrows = []
        
        for item in scene.selectedItems():
            if hasattr(item, 'get_text'):
                if hasattr(item, 'get_source'):  # It's an arrow
                    selected_arrows.append(item)
                else:  # It's an object
                    selected_objects.append(item)
        
        try:
            # Create proof step instance
            proof_step = proof_step_class(scene, selected_objects, selected_arrows)
            
            # Import and create the command
            from core.undo_commands import ProofStepCommand
            command = ProofStepCommand(
                proof_step=proof_step,
                description=f"Apply {proof_step_class.__name__}"
            )
            
            # Execute via global undo stack
            from PyQt6.QtWidgets import QApplication
            app = QApplication.instance()
            if hasattr(app, 'undo_stack'):
                app.undo_stack.push(command)
                
                # Clear the overlay immediately after successful execution
                # The diagram state has changed, so current buttons are no longer valid
                self.button_panel.clear_buttons()
                self.hide()
            else:
                print("Warning: App has no undo_stack")
                
        except Exception as e:
            print(f"Error executing proof step: {e}")
            import traceback
            traceback.print_exc()
    
    def mousePressEvent(self, event):
        """Forward mouse events to diagram view if not on button panel."""
        # Check if the event is on the button panel
        button_panel_rect = self.button_panel.geometry()
        if button_panel_rect.contains(event.pos()):
            # Let the button panel handle it
            super().mousePressEvent(event)
        else:
            # Forward to diagram view - convert QPoint to QPointF
            from PyQt6.QtCore import QPointF
            view_pos = QPointF(event.pos())
            new_event = event.__class__(
                event.type(),
                view_pos,
                event.button(),
                event.buttons(),
                event.modifiers()
            )
            self.diagram_view.mousePressEvent(new_event)
    
    def mouseMoveEvent(self, event):
        """Forward mouse move events to diagram view if not on button panel."""
        button_panel_rect = self.button_panel.geometry()
        if not button_panel_rect.contains(event.pos()):
            from PyQt6.QtCore import QPointF
            view_pos = QPointF(event.pos())
            new_event = event.__class__(
                event.type(),
                view_pos,
                event.button(),
                event.buttons(),
                event.modifiers()
            )
            self.diagram_view.mouseMoveEvent(new_event)
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Forward mouse release events to diagram view if not on button panel."""
        button_panel_rect = self.button_panel.geometry()
        if button_panel_rect.contains(event.pos()):
            # Let the button panel handle it
            super().mouseReleaseEvent(event)
        else:
            # Forward to diagram view
            from PyQt6.QtCore import QPointF
            view_pos = QPointF(event.pos())
            new_event = event.__class__(
                event.type(),
                view_pos,
                event.button(),
                event.buttons(),
                event.modifiers()
            )
            self.diagram_view.mouseReleaseEvent(new_event)
