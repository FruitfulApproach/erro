"""
Element rename dialog for selecting Greek letters and adding prime marks.
"""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QPushButton, QLineEdit, QLabel, QDialogButtonBox)
from PyQt6.QtCore import Qt


class ElementRenameDialog(QDialog):
    """Dialog for selecting element names using Greek letters and prime marks."""
    
    def __init__(self, current_name="x", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Element")
        self.setModal(True)
        self.resize(450, 350)
        
        # Store the current name being built
        self._current_name = current_name
        
        self.setup_ui()
        self.update_display()
        
    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        
        # Title label
        title_label = QLabel("Select a Greek letter for the element:")
        layout.addWidget(title_label)
        
        # Display current name (read-only)
        self.name_display = QLineEdit()
        self.name_display.setReadOnly(True)
        self.name_display.setStyleSheet("QLineEdit { background-color: #f0f0f0; font-size: 16px; font-weight: bold; }")
        layout.addWidget(self.name_display)
        
        # Button controls layout
        controls_layout = QHBoxLayout()
        
        # Clear button
        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self.clear_name)
        controls_layout.addWidget(self.clear_button)
        
        # Prime button
        self.prime_button = QPushButton("Add ' (Prime)")
        self.prime_button.clicked.connect(self.add_prime)
        controls_layout.addWidget(self.prime_button)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        # Greek letters grid
        self.create_greek_letters_grid(layout)
        
        # Standard dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
    def create_greek_letters_grid(self, parent_layout):
        """Create a grid of Greek letter buttons."""
        greek_layout = QVBoxLayout()
        
        # Greek letters (lowercase only as requested)
        greek_letters = [
            ['α', 'β', 'γ', 'δ', 'ε', 'ζ'],
            ['η', 'θ', 'ι', 'κ', 'λ', 'μ'],
            ['ν', 'ξ', 'ο', 'π', 'ρ', 'σ'],
            ['τ', 'υ', 'φ', 'χ', 'ψ', 'ω']
        ]
        
        grid = QGridLayout()
        
        for row, letters in enumerate(greek_letters):
            for col, letter in enumerate(letters):
                button = QPushButton(letter)
                button.setMinimumSize(40, 40)
                button.setStyleSheet("QPushButton { font-size: 16px; font-weight: bold; }")
                button.clicked.connect(lambda checked, l=letter: self.set_base_letter(l))
                grid.addWidget(button, row, col)
        
        greek_layout.addWidget(QLabel("Greek Letters:"))
        greek_layout.addLayout(grid)
        parent_layout.addLayout(greek_layout)
        
    def set_base_letter(self, letter):
        """Set the base letter (removes any existing primes)."""
        self._current_name = letter
        self.update_display()
        
    def add_prime(self):
        """Add a prime mark to the current name."""
        self._current_name += "'"
        self.update_display()
        
    def clear_name(self):
        """Clear the current name and reset to default."""
        self._current_name = "x"
        self.update_display()
        
    def update_display(self):
        """Update the name display field."""
        self.name_display.setText(self._current_name)
        
    def get_element_name(self):
        """Return the selected element name."""
        return self._current_name
