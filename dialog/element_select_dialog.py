"""
Element selection dialog for selecting elements from a comma-separated list.
"""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QPushButton, QLabel, QDialogButtonBox)
from PyQt6.QtCore import Qt


class ElementSelectDialog(QDialog):
    """Dialog for selecting an element from a comma-separated list."""
    
    def __init__(self, elements_text, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Element")
        self.setModal(True)
        
        # Parse elements from the text (everything before the first colon)
        self.elements = self._parse_elements(elements_text)
        self.selected_element = None
        
        self.setup_ui()
        
    def _parse_elements(self, text):
        """Parse comma-separated elements from text before the first colon."""
        if ':' in text:
            elements_part = text.split(':', 1)[0]
        else:
            elements_part = text
            
        # Split by comma and clean up whitespace
        elements = [elem.strip() for elem in elements_part.split(',') if elem.strip()]
        return elements
    
    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        
        # Title label
        title_label = QLabel("Select an element to map:")
        layout.addWidget(title_label)
        
        # Elements grid layout
        grid_layout = QGridLayout()
        
        # Create buttons for each element
        row = 0
        col = 0
        max_cols = 4  # Maximum buttons per row
        
        for element in self.elements:
            button = QPushButton(element)
            button.clicked.connect(lambda checked, elem=element: self._select_element(elem))
            button.setMinimumHeight(40)
            button.setMinimumWidth(80)
            
            grid_layout.addWidget(button, row, col)
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
        
        layout.addLayout(grid_layout)
        
        # Cancel button
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # Resize dialog based on content
        self._resize_dialog(len(self.elements))
        
    def _resize_dialog(self, element_count):
        """Resize dialog based on number of elements."""
        if element_count <= 4:
            self.resize(400, 150)
        elif element_count <= 8:
            self.resize(400, 200)
        else:
            self.resize(500, 250)
    
    def _select_element(self, element):
        """Handle element selection."""
        self.selected_element = element
        self.accept()
        
    def get_selected_element(self):
        """Get the selected element name."""
        return self.selected_element