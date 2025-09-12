"""
Main window for the DAG diagram application.
"""
from PyQt6.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QWidget, QToolBar, QPushButton, QLabel,
                             QStatusBar, QMenuBar, QMenu, QMessageBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QKeySequence

from diagram_scene import DiagramScene
from diagram_view import DiagramView


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Pythom - DAG Diagram Editor")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create the diagram scene and view
        self.scene = DiagramScene(self)
        self.view = DiagramView(self.scene, self)
        
        # Set the central widget
        self.setCentralWidget(self.view)
        
        # Create UI components
        self.create_menus()
        self.create_toolbar()
        self.create_status_bar()
        
        # Connect signals
        self.scene.object_added.connect(self.on_object_added)
        
    def create_menus(self):
        """Create the menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        new_action = QAction("&New", self)
        new_action.setShortcut(QKeySequence.StandardKey.New)
        new_action.triggered.connect(self.new_diagram)
        file_menu.addAction(new_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu("&Edit")
        
        # Get the global undo stack
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance()
        undo_stack = app.undo_stack
        
        # Add undo action
        undo_action = undo_stack.createUndoAction(self, "&Undo")
        undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        edit_menu.addAction(undo_action)
        
        # Add redo action
        redo_action = undo_stack.createRedoAction(self, "&Redo")
        redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        edit_menu.addAction(redo_action)
        
        # Add separator
        edit_menu.addSeparator()
        
        # Add delete action
        delete_action = QAction("&Delete", self)
        delete_action.setShortcut(QKeySequence.StandardKey.Delete)
        delete_action.triggered.connect(self.delete_selected_items)
        edit_menu.addAction(delete_action)
        
        # View menu
        view_menu = menubar.addMenu("&View")
        
        zoom_in_action = QAction("Zoom &In", self)
        zoom_in_action.setShortcut(QKeySequence.StandardKey.ZoomIn)
        zoom_in_action.triggered.connect(self.zoom_in)
        view_menu.addAction(zoom_in_action)
        
        zoom_out_action = QAction("Zoom &Out", self)
        zoom_out_action.setShortcut(QKeySequence.StandardKey.ZoomOut)
        zoom_out_action.triggered.connect(self.zoom_out)
        view_menu.addAction(zoom_out_action)
        
        reset_zoom_action = QAction("&Reset Zoom", self)
        reset_zoom_action.setShortcut("Ctrl+0")
        reset_zoom_action.triggered.connect(self.view.reset_zoom)
        view_menu.addAction(reset_zoom_action)
        
        view_menu.addSeparator()
        
        fit_all_action = QAction("&Fit All", self)
        fit_all_action.setShortcut("Ctrl+F")
        fit_all_action.triggered.connect(self.view.fit_in_view_all)
        view_menu.addAction(fit_all_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def create_toolbar(self):
        """Create the toolbar."""
        toolbar = QToolBar("Main Toolbar", self)
        self.addToolBar(toolbar)
        
        # New diagram button
        new_btn = QPushButton("New", self)
        new_btn.clicked.connect(self.new_diagram)
        toolbar.addWidget(new_btn)
        
        toolbar.addSeparator()
        
        # Zoom buttons
        zoom_in_btn = QPushButton("Zoom In", self)
        zoom_in_btn.clicked.connect(self.zoom_in)
        toolbar.addWidget(zoom_in_btn)
        
        zoom_out_btn = QPushButton("Zoom Out", self)
        zoom_out_btn.clicked.connect(self.zoom_out)
        toolbar.addWidget(zoom_out_btn)
        
        reset_zoom_btn = QPushButton("Reset Zoom", self)
        reset_zoom_btn.clicked.connect(self.view.reset_zoom)
        toolbar.addWidget(reset_zoom_btn)
        
        toolbar.addSeparator()
        
        # Fit all button
        fit_all_btn = QPushButton("Fit All", self)
        fit_all_btn.clicked.connect(self.view.fit_in_view_all)
        toolbar.addWidget(fit_all_btn)
        
    def create_status_bar(self):
        """Create the status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Add permanent widgets to status bar
        self.zoom_label = QLabel("Zoom: 100%")
        self.status_bar.addPermanentWidget(self.zoom_label)
        
        self.coordinates_label = QLabel("Position: (0, 0)")
        self.status_bar.addPermanentWidget(self.coordinates_label)
        
        # Initial message
        self.status_bar.showMessage("Ready. Double-click canvas for objects, objects for arrows. Right-click for options and labels.")
        
    def new_diagram(self):
        """Create a new diagram."""
        self.scene.clear()
        self.view.reset_zoom()
        self.status_bar.showMessage("New diagram created. Double-click canvas for objects, objects for arrows. Right-click for options and labels.")
        
    def zoom_in(self):
        """Zoom in the view."""
        current_zoom = self.view.get_zoom_level()
        if current_zoom < 5.0:
            self.view.scale(1.15, 1.15)
            self.update_zoom_label()
            
    def zoom_out(self):
        """Zoom out the view."""
        current_zoom = self.view.get_zoom_level()
        if current_zoom > 0.1:
            self.view.scale(1/1.15, 1/1.15)
            self.update_zoom_label()
            
    def update_zoom_label(self):
        """Update the zoom level display in status bar."""
        zoom_percent = int(self.view.get_zoom_level() * 100)
        self.zoom_label.setText(f"Zoom: {zoom_percent}%")
        
    def on_object_added(self, obj):
        """Handle when an object is added to the scene."""
        object_count = len([item for item in self.scene.items() 
                           if hasattr(item, 'get_text')])
        self.status_bar.showMessage(f"Object added. Total objects: {object_count}")
        
    def show_about(self):
        """Show about dialog."""
        QMessageBox.about(self, "About Pythom", 
                         "Pythom - DAG Diagram Editor\n\n"
                         "A PyQt6-based application for creating and editing\n"
                         "Directed Acyclic Graph (DAG) diagrams.\n\n"
                         "• Double-click on the canvas to add objects\n"
                         "• Double-click on objects to start creating arrows\n"
                         "• Double-click same object twice to create self-loop\n"
                         "• While creating arrows, double-click empty space to create new target object\n"
                         "• Parallel arrows automatically curve to avoid overlap\n"
                         "• Objects cannot occupy the same grid position\n"
                         "• Select items and press DEL to delete them\n"
                         "• Right-click on objects/arrows to edit their names\n"
                         "• Right-click on empty space to add text labels\n"
                         "• Objects snap to a 100x100 grid\n"
                         "• Node names: A, B, C, ..., Z, A', B', etc.\n"
                         "• Arrow names: a, b, c, ..., z, a', b', etc.\n"
                         "• Full undo/redo support with Ctrl+Z/Ctrl+Y\n"
                         "• Press ESC or right-click to cancel arrow creation")
    
    def delete_selected_items(self):
        """Delete the currently selected items from the scene."""
        # Get selected items from the scene
        selected_items = self.scene.selectedItems()
        
        if not selected_items:
            return  # Nothing to delete
        
        # Filter out items that shouldn't be deleted (like temporary items)
        deletable_items = []
        for item in selected_items:
            # Include Objects, Arrows, and AdditionalLabels
            if (hasattr(item, 'get_text') or  # Objects and Arrows
                hasattr(item, 'toPlainText')):  # AdditionalLabels
                deletable_items.append(item)
        
        if not deletable_items:
            return  # Nothing deletable selected
        
        # Create and execute delete command
        from undo_commands import DeleteItems
        from PyQt6.QtWidgets import QApplication
        
        command = DeleteItems(self.scene, deletable_items)
        app = QApplication.instance()
        app.undo_stack.push(command)
        
        # Update status bar
        if len(deletable_items) == 1:
            item = deletable_items[0]
            if hasattr(item, 'get_text'):
                item_name = item.get_text()
                item_type = "Object" if hasattr(item, 'boundingRect') and item.type() == 65537 else "Arrow"
                self.status_bar.showMessage(f"Deleted {item_type} '{item_name}'.")
            else:
                self.status_bar.showMessage("Deleted item.")
        else:
            self.status_bar.showMessage(f"Deleted {len(deletable_items)} items.")
        
    def closeEvent(self, event):
        """Handle application close event."""
        # Could add save confirmation here if needed
        event.accept()
