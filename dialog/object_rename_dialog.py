"""
Object rename dialog for changing node names using letter buttons.
"""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QPushButton, QLineEdit, QLabel, QDialogButtonBox)
from PyQt6.QtCore import Qt


class ObjectRenameDialog(QDialog):
    """Dialog for renaming objects using letter buttons and prime marks."""
    
    def __init__(self, current_name="A", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Rename Object")
        self.setModal(True)
        self.resize(400, 300)
        
        # Store the current name being built
        self._current_name = current_name
        
        self.setup_ui()
        self.update_display()
        
    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        
        # Title label
        title_label = QLabel("Click letters to build the new name:")
        layout.addWidget(title_label)
        
        # Display current name (read-only)
        self.name_display = QLineEdit()
        self.name_display.setReadOnly(True)
        self.name_display.setStyleSheet("QLineEdit { background-color: #f0f0f0; font-size: 14px; font-weight: bold; }")
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
        
        # Backspace button
        self.backspace_button = QPushButton("⌫ Backspace")
        self.backspace_button.clicked.connect(self.backspace)
        controls_layout.addWidget(self.backspace_button)
        
        layout.addLayout(controls_layout)
        
        # Letter buttons grid (A-Z) + "0"
        letter_grid = QGridLayout()
        
        # Create buttons for A-Z in a 4x7 grid (26 letters + 2 empty spaces)
        letters = [chr(ord('A') + i) for i in range(26)]
        
        for i, letter in enumerate(letters):
            row = i // 7
            col = i % 7
            
            button = QPushButton(letter)
            button.setMinimumSize(40, 40)
            button.clicked.connect(lambda checked, l=letter: self.set_letter(l))
            letter_grid.addWidget(button, row, col)
        
        # Add "0" button in the next available position
        zero_button = QPushButton("0")
        zero_button.setMinimumSize(40, 40)
        zero_button.clicked.connect(lambda checked: self.set_letter("0"))
        # Position after the 26 letters (row 3, col 5)
        letter_grid.addWidget(zero_button, 3, 5)
        
        layout.addLayout(letter_grid)
        
        # Global rename checkbox
        from PyQt6.QtWidgets import QCheckBox
        self.global_rename_checkbox = QCheckBox("Replace all occurrences throughout the diagram")
        self.global_rename_checkbox.setToolTip("If checked, replaces this name everywhere it appears on arrows and objects")
        layout.addWidget(self.global_rename_checkbox)
        
        # Dialog buttons (OK/Cancel)
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
    def set_letter(self, letter):
        """Set the base letter, removing any existing letters but keeping primes."""
        # Count existing primes
        prime_count = self._current_name.count("'")
        
        # Set new name to just the letter plus existing primes
        self._current_name = letter + ("'" * prime_count)
        self.update_display()
        
    def add_prime(self):
        """Add a prime mark to the current name."""
        self._current_name += "'"
        self.update_display()
        
    def clear_name(self):
        """Clear the current name."""
        self._current_name = ""
        self.update_display()
        
    def backspace(self):
        """Remove the last character from the current name."""
        if self._current_name:
            self._current_name = self._current_name[:-1]
            self.update_display()
    
    def update_display(self):
        """Update the display of the current name."""
        display_text = self._current_name if self._current_name else "(empty)"
        self.name_display.setText(display_text)
        
        # Enable/disable buttons based on current state
        has_content = bool(self._current_name)
        self.clear_button.setEnabled(has_content)
        self.backspace_button.setEnabled(has_content)
        
        # Enable prime button if we have at least one letter or "0"
        has_valid_symbol = any(c.isalpha() or c == '0' for c in self._current_name)
        self.prime_button.setEnabled(has_valid_symbol)
    
    def get_name(self):
        """Get the current name."""
        return self._current_name
    
    def get_global_rename(self):
        """Get the state of the global rename checkbox."""
        return self.global_rename_checkbox.isChecked()
    
    def set_name(self, name):
        """Set the current name."""
        self._current_name = name
        self.update_display()
