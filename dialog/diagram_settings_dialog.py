"""
Diagram Settings dialog for configuring diagram appearance and behavior.
"""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
                             QWidget, QLabel, QSpinBox, QDoubleSpinBox,
                             QColorDialog, QPushButton, QGroupBox, QFormLayout,
                             QSlider, QCheckBox, QComboBox, QGridLayout)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPalette, QIcon


class ColorButton(QPushButton):
    """Custom button for color selection."""
    
    colorChanged = pyqtSignal(QColor)
    
    def __init__(self, color=QColor(0, 0, 0), parent=None):
        super().__init__(parent)
        self._color = color
        self.setFixedSize(50, 30)
        self.clicked.connect(self.choose_color)
        self.update_color_display()
    
    def update_color_display(self):
        """Update the button appearance to show the current color."""
        self.setStyleSheet(f"background-color: {self._color.name()}; border: 1px solid gray;")
    
    def choose_color(self):
        """Open color dialog to choose a new color."""
        color = QColorDialog.getColor(self._color, self, "Choose Color")
        if color.isValid():
            self._color = color
            self.update_color_display()
            self.colorChanged.emit(color)
    
    def get_color(self):
        """Get the current color."""
        return self._color
    
    def set_color(self, color):
        """Set the current color."""
        self._color = color
        self.update_color_display()


class DiagramSettingsDialog(QDialog):
    """Dialog for configuring diagram settings."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Diagram Settings")
        self.setModal(True)
        self.resize(500, 400)
        
        # Store original settings for reset functionality
        self._original_settings = {}
        
        # Create main layout
        main_layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Create tabs
        self.create_appearance_tab()
        self.create_grid_tab()
        self.create_objects_tab()
        self.create_arrows_tab()
        
        # Create button layout
        button_layout = QHBoxLayout()
        
        # Reset button
        reset_button = QPushButton("Reset to Defaults")
        reset_button.clicked.connect(self.reset_to_defaults)
        button_layout.addWidget(reset_button)
        
        button_layout.addStretch()
        
        # OK and Cancel buttons
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        ok_button.setDefault(True)
        button_layout.addWidget(ok_button)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        main_layout.addLayout(button_layout)
        
        # Load current settings
        self.load_current_settings()
    
    def create_appearance_tab(self):
        """Create the Appearance settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Background group
        bg_group = QGroupBox("Background")
        bg_layout = QFormLayout(bg_group)
        
        # Background color
        self.bg_color_button = ColorButton(QColor(255, 255, 255))
        bg_layout.addRow("Background Color:", self.bg_color_button)
        
        # Selection color
        self.selection_color_button = ColorButton(QColor(255, 165, 0))
        bg_layout.addRow("Selection Color:", self.selection_color_button)
        
        layout.addWidget(bg_group)
        
        # Text group
        text_group = QGroupBox("Text Settings")
        text_layout = QFormLayout(text_group)
        
        # Font size
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(6, 24)
        self.font_size_spin.setValue(12)
        self.font_size_spin.setSuffix(" pt")
        text_layout.addRow("Default Font Size:", self.font_size_spin)
        
        # Text color
        self.text_color_button = ColorButton(QColor(0, 0, 0))
        text_layout.addRow("Text Color:", self.text_color_button)
        
        layout.addWidget(text_group)
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "Appearance")
    
    def create_grid_tab(self):
        """Create the Grid settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Grid group
        grid_group = QGroupBox("Grid Settings")
        grid_layout = QFormLayout(grid_group)
        
        # Grid spacing
        self.grid_spacing_spin = QSpinBox()
        self.grid_spacing_spin.setRange(50, 500)
        self.grid_spacing_spin.setValue(150)
        self.grid_spacing_spin.setSuffix(" px")
        grid_layout.addRow("Grid Spacing:", self.grid_spacing_spin)
        
        # Show grid
        self.show_grid_check = QCheckBox("Show Grid Lines")
        grid_layout.addRow("", self.show_grid_check)
        
        # Grid color
        self.grid_color_button = ColorButton(QColor(200, 200, 200))
        grid_layout.addRow("Grid Color:", self.grid_color_button)
        
        # Grid line width
        self.grid_width_spin = QDoubleSpinBox()
        self.grid_width_spin.setRange(0.1, 5.0)
        self.grid_width_spin.setValue(1.0)
        self.grid_width_spin.setSuffix(" px")
        self.grid_width_spin.setDecimals(1)
        grid_layout.addRow("Grid Line Width:", self.grid_width_spin)
        
        layout.addWidget(grid_group)
        
        # Snap group
        snap_group = QGroupBox("Snap Settings")
        snap_layout = QFormLayout(snap_group)
        
        # Snap to grid
        self.snap_to_grid_check = QCheckBox("Snap Objects to Grid")
        self.snap_to_grid_check.setChecked(True)
        snap_layout.addRow("", self.snap_to_grid_check)
        
        layout.addWidget(snap_group)
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "Grid")
    
    def create_objects_tab(self):
        """Create the Objects settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Object appearance group
        obj_group = QGroupBox("Object Appearance")
        obj_layout = QFormLayout(obj_group)
        
        # Object border color
        self.obj_border_color_button = ColorButton(QColor(0, 0, 0))
        obj_layout.addRow("Border Color:", self.obj_border_color_button)
        
        # Object fill color
        self.obj_fill_color_button = ColorButton(QColor(0, 0, 0, 0))  # Transparent
        obj_layout.addRow("Fill Color:", self.obj_fill_color_button)
        
        # Object border width
        self.obj_border_width_spin = QDoubleSpinBox()
        self.obj_border_width_spin.setRange(0, 10)
        self.obj_border_width_spin.setValue(0)
        self.obj_border_width_spin.setSuffix(" px")
        self.obj_border_width_spin.setDecimals(1)
        obj_layout.addRow("Border Width:", self.obj_border_width_spin)
        
        # Corner radius
        self.corner_radius_spin = QSpinBox()
        self.corner_radius_spin.setRange(0, 50)
        self.corner_radius_spin.setValue(10)
        self.corner_radius_spin.setSuffix(" px")
        obj_layout.addRow("Corner Radius:", self.corner_radius_spin)
        
        layout.addWidget(obj_group)
        
        # Object sizing group
        size_group = QGroupBox("Object Sizing")
        size_layout = QFormLayout(size_group)
        
        # Minimum width
        self.min_width_spin = QSpinBox()
        self.min_width_spin.setRange(20, 200)
        self.min_width_spin.setValue(80)
        self.min_width_spin.setSuffix(" px")
        size_layout.addRow("Minimum Width:", self.min_width_spin)
        
        # Minimum height
        self.min_height_spin = QSpinBox()
        self.min_height_spin.setRange(20, 200)
        self.min_height_spin.setValue(80)
        self.min_height_spin.setSuffix(" px")
        size_layout.addRow("Minimum Height:", self.min_height_spin)
        
        # Padding
        self.obj_padding_spin = QSpinBox()
        self.obj_padding_spin.setRange(2, 50)
        self.obj_padding_spin.setValue(10)
        self.obj_padding_spin.setSuffix(" px")
        size_layout.addRow("Text Padding:", self.obj_padding_spin)
        
        layout.addWidget(size_group)
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "Objects")
    
    def create_arrows_tab(self):
        """Create the Arrows settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Arrow appearance group
        arrow_group = QGroupBox("Arrow Appearance")
        arrow_layout = QFormLayout(arrow_group)
        
        # Arrow color
        self.arrow_color_button = ColorButton(QColor(100, 100, 100))
        arrow_layout.addRow("Arrow Color:", self.arrow_color_button)
        
        # Arrow line width
        self.arrow_width_spin = QDoubleSpinBox()
        self.arrow_width_spin.setRange(0.5, 10.0)
        self.arrow_width_spin.setValue(2.0)
        self.arrow_width_spin.setSuffix(" px")
        self.arrow_width_spin.setDecimals(1)
        arrow_layout.addRow("Line Width:", self.arrow_width_spin)
        
        layout.addWidget(arrow_group)
        
        # Arrow head group
        head_group = QGroupBox("Arrow Head")
        head_layout = QFormLayout(head_group)
        
        # Arrow head size
        self.arrow_head_size_spin = QSpinBox()
        self.arrow_head_size_spin.setRange(5, 50)
        self.arrow_head_size_spin.setValue(15)
        self.arrow_head_size_spin.setSuffix(" px")
        head_layout.addRow("Head Size:", self.arrow_head_size_spin)
        
        # Arrow head angle
        self.arrow_head_angle_spin = QSpinBox()
        self.arrow_head_angle_spin.setRange(15, 60)
        self.arrow_head_angle_spin.setValue(30)
        self.arrow_head_angle_spin.setSuffix("°")
        head_layout.addRow("Head Angle:", self.arrow_head_angle_spin)
        
        layout.addWidget(head_group)
        
        # Curve settings group
        curve_group = QGroupBox("Curve Settings")
        curve_layout = QFormLayout(curve_group)
        
        # Curve intensity for parallel arrows
        self.curve_intensity_spin = QSpinBox()
        self.curve_intensity_spin.setRange(10, 100)
        self.curve_intensity_spin.setValue(30)
        self.curve_intensity_spin.setSuffix(" px")
        curve_layout.addRow("Parallel Curve Offset:", self.curve_intensity_spin)
        
        # Self-loop radius
        self.self_loop_radius_spin = QSpinBox()
        self.self_loop_radius_spin.setRange(20, 100)
        self.self_loop_radius_spin.setValue(50)
        self.self_loop_radius_spin.setSuffix(" px")
        curve_layout.addRow("Self-loop Radius:", self.self_loop_radius_spin)
        
        layout.addWidget(curve_group)
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "Arrows")
    
    def load_current_settings(self):
        """Load current settings from the application."""
        # This would typically load from the main window or scene
        # For now, we'll use defaults that match the current implementation
        pass
    
    def reset_to_defaults(self):
        """Reset all settings to default values."""
        # Appearance
        self.bg_color_button.set_color(QColor(255, 255, 255))
        self.selection_color_button.set_color(QColor(255, 165, 0))
        self.font_size_spin.setValue(12)
        self.text_color_button.set_color(QColor(0, 0, 0))
        
        # Grid
        self.grid_spacing_spin.setValue(150)
        self.show_grid_check.setChecked(False)
        self.grid_color_button.set_color(QColor(200, 200, 200))
        self.grid_width_spin.setValue(1.0)
        self.snap_to_grid_check.setChecked(True)
        
        # Objects
        self.obj_border_color_button.set_color(QColor(0, 0, 0))
        self.obj_fill_color_button.set_color(QColor(0, 0, 0, 0))
        self.obj_border_width_spin.setValue(0.0)
        self.corner_radius_spin.setValue(10)
        self.min_width_spin.setValue(80)
        self.min_height_spin.setValue(80)
        self.obj_padding_spin.setValue(10)
        
        # Arrows
        self.arrow_color_button.set_color(QColor(100, 100, 100))
        self.arrow_width_spin.setValue(2.0)
        self.arrow_head_size_spin.setValue(15)
        self.arrow_head_angle_spin.setValue(30)
        self.curve_intensity_spin.setValue(30)
        self.self_loop_radius_spin.setValue(50)
    
    def get_settings(self):
        """Get all current settings as a dictionary."""
        return {
            # Appearance
            'bg_color': self.bg_color_button.get_color(),
            'selection_color': self.selection_color_button.get_color(),
            'font_size': self.font_size_spin.value(),
            'text_color': self.text_color_button.get_color(),
            
            # Grid
            'grid_spacing': self.grid_spacing_spin.value(),
            'show_grid': self.show_grid_check.isChecked(),
            'grid_color': self.grid_color_button.get_color(),
            'grid_width': self.grid_width_spin.value(),
            'snap_to_grid': self.snap_to_grid_check.isChecked(),
            
            # Objects
            'obj_border_color': self.obj_border_color_button.get_color(),
            'obj_fill_color': self.obj_fill_color_button.get_color(),
            'obj_border_width': self.obj_border_width_spin.value(),
            'corner_radius': self.corner_radius_spin.value(),
            'min_width': self.min_width_spin.value(),
            'min_height': self.min_height_spin.value(),
            'obj_padding': self.obj_padding_spin.value(),
            
            # Arrows
            'arrow_color': self.arrow_color_button.get_color(),
            'arrow_width': self.arrow_width_spin.value(),
            'arrow_head_size': self.arrow_head_size_spin.value(),
            'arrow_head_angle': self.arrow_head_angle_spin.value(),
            'curve_intensity': self.curve_intensity_spin.value(),
            'self_loop_radius': self.self_loop_radius_spin.value(),
        }
    
    def set_settings(self, settings):
        """Set settings from a dictionary."""
        # Appearance
        if 'bg_color' in settings:
            self.bg_color_button.set_color(settings['bg_color'])
        if 'selection_color' in settings:
            self.selection_color_button.set_color(settings['selection_color'])
        if 'font_size' in settings:
            self.font_size_spin.setValue(settings['font_size'])
        if 'text_color' in settings:
            self.text_color_button.set_color(settings['text_color'])
        
        # Grid
        if 'grid_spacing' in settings:
            self.grid_spacing_spin.setValue(settings['grid_spacing'])
        if 'show_grid' in settings:
            self.show_grid_check.setChecked(settings['show_grid'])
        if 'grid_color' in settings:
            self.grid_color_button.set_color(settings['grid_color'])
        if 'grid_width' in settings:
            self.grid_width_spin.setValue(settings['grid_width'])
        if 'snap_to_grid' in settings:
            self.snap_to_grid_check.setChecked(settings['snap_to_grid'])
        
        # Objects
        if 'obj_border_color' in settings:
            self.obj_border_color_button.set_color(settings['obj_border_color'])
        if 'obj_fill_color' in settings:
            self.obj_fill_color_button.set_color(settings['obj_fill_color'])
        if 'obj_border_width' in settings:
            self.obj_border_width_spin.setValue(settings['obj_border_width'])
        if 'corner_radius' in settings:
            self.corner_radius_spin.setValue(settings['corner_radius'])
        if 'min_width' in settings:
            self.min_width_spin.setValue(settings['min_width'])
        if 'min_height' in settings:
            self.min_height_spin.setValue(settings['min_height'])
        if 'obj_padding' in settings:
            self.obj_padding_spin.setValue(settings['obj_padding'])
        
        # Arrows
        if 'arrow_color' in settings:
            self.arrow_color_button.set_color(settings['arrow_color'])
        if 'arrow_width' in settings:
            self.arrow_width_spin.setValue(settings['arrow_width'])
        if 'arrow_head_size' in settings:
            self.arrow_head_size_spin.setValue(settings['arrow_head_size'])
        if 'arrow_head_angle' in settings:
            self.arrow_head_angle_spin.setValue(settings['arrow_head_angle'])
        if 'curve_intensity' in settings:
            self.curve_intensity_spin.setValue(settings['curve_intensity'])
        if 'self_loop_radius' in settings:
            self.self_loop_radius_spin.setValue(settings['self_loop_radius'])
