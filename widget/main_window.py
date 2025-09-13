"""
Main window for the DAG diagram application.
"""
import os
from PyQt6.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QWidget, QToolBar, QPushButton, QLabel,
                             QStatusBar, QMenuBar, QMenu, QMessageBox, QTabWidget,
                             QFileDialog, QApplication)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QKeySequence, QColor

from .diagram_scene import DiagramScene
from .diagram_view import DiagramView
from core.session_manager import SessionManager


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Pythom - DAG Diagram Editor")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create tab widget as central widget
        self.tab_widget = QTabWidget(self)
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.setCentralWidget(self.tab_widget)
        
        # Keep track of diagram counter for naming
        self.diagram_counter = 0
        
        # File handling
        self.current_file = None
        self.is_modified = False
        
        # Initialize session manager
        self.session_manager = SessionManager()
        
        # Track geometry changes for saving
        self._geometry_timer = None
        
        # Initialize diagram settings with defaults
        self.diagram_settings = {
            # Appearance
            'bg_color': QColor(255, 255, 255),
            'selection_color': QColor(255, 165, 0),
            'font_size': 14,
            'text_color': QColor(0, 0, 0),
            
            # Grid
            'grid_spacing': 150,
            'show_grid': False,
            'grid_color': QColor(200, 200, 200),
            'grid_width': 1.0,
            'snap_to_grid': True,
            'auto_grid_spacing': True,
            
            # Objects
            'obj_border_color': QColor(0, 0, 0),
            'obj_fill_color': QColor(0, 0, 0, 0),
            'obj_border_width': 0.0,
            'corner_radius': 10,
            'min_width': 80,
            'min_height': 80,
            'obj_padding': 10,
            
            # Arrows
            'arrow_color': QColor(100, 100, 100),
            'arrow_width': 2.0,
            'arrow_head_size': 15,
            'arrow_head_angle': 30,
            'curve_intensity': 30,
            'self_loop_radius': 50,
        }
        
        # Create the first diagram tab
        self.create_new_diagram()
        
        # Create UI components
        self.create_menus()
        self.create_toolbar()
        self.create_status_bar()
        
        # Connect signals
        if self.get_current_scene():
            self.get_current_scene().object_added.connect(self.on_object_added)
    
    def get_math_calligraphy_name(self, index):
        """Get math-calligraphy Unicode letter for diagram naming."""
        # Math-calligraphy Unicode letters (𝒜, ℬ, 𝒞, 𝒟, ...)
        math_cal_base = {
            'A': '𝒜', 'B': 'ℬ', 'C': '𝒞', 'D': '𝒟', 'E': 'ℰ', 'F': 'ℱ', 'G': '𝒢', 'H': 'ℋ',
            'I': 'ℐ', 'J': '𝒥', 'K': '𝒦', 'L': 'ℒ', 'M': 'ℳ', 'N': '𝒩', 'O': '𝒪', 'P': '𝒫',
            'Q': '𝒬', 'R': 'ℛ', 'S': '𝒮', 'T': '𝒯', 'U': '𝒰', 'V': '𝒱', 'W': '𝒲', 'X': '𝒳',
            'Y': '𝒴', 'Z': '𝒵'
        }
        
        # Calculate apostrophe count and letter index
        apostrophe_count = index // 26
        letter_index = index % 26
        letter = chr(ord('A') + letter_index)
        
        # Get math-calligraphy letter and add apostrophes
        math_cal_letter = math_cal_base[letter]
        apostrophes = "'" * apostrophe_count
        
        return math_cal_letter + apostrophes
    
    def create_new_diagram(self):
        """Create a new diagram in a new tab."""
        # Create new scene and view
        scene = DiagramScene(self)
        view = DiagramView(scene, self)
        
        # Apply current settings to new diagram
        self.apply_settings_to_new_diagram(scene, view)
        
        # Get diagram name
        diagram_name = self.get_math_calligraphy_name(self.diagram_counter)
        self.diagram_counter += 1
        
        # Add tab
        tab_index = self.tab_widget.addTab(view, diagram_name)
        self.tab_widget.setCurrentIndex(tab_index)
        
        # Connect scene signals for modification tracking
        scene.object_added.connect(self.on_object_added)
        scene.changed.connect(self.mark_modified)  # Mark as modified on any scene change
        
        return scene, view
    
    def close_tab(self, index):
        """Close a tab and properly clean up the DiagramScene."""
        if index < 0 or index >= self.tab_widget.count():
            return
        
        # Get the widget (DiagramView) and scene before removing
        widget = self.tab_widget.widget(index)
        if widget:
            scene = widget.scene()
            
            # Clean up the scene properly
            if scene:
                # Clear all items from the scene
                scene.clear()
                
                # Disconnect modification tracking signals
                try:
                    scene.object_added.disconnect(self.on_object_added)
                except TypeError:
                    pass  # No connections to disconnect
                
                try:
                    scene.changed.disconnect(self.mark_modified)
                except TypeError:
                    pass  # No connections to disconnect
                
                # If the scene has any timers, stop them
                if hasattr(scene, '_validation_timer'):
                    scene._validation_timer.stop()
        
        if self.tab_widget.count() > 1:
            # Remove the tab
            self.tab_widget.removeTab(index)
            
            # Mark as modified so session data gets updated
            self.is_modified = True
        else:
            # Don't close the last tab, just clear it and reset the name
            if widget and widget.scene():
                widget.scene().clear()
                # Reset tab name to default
                self.tab_widget.setTabText(index, self.get_math_calligraphy_name(0))
            
            # Mark as modified
            self.is_modified = True
    
    def get_current_scene(self):
        """Get the currently active scene."""
        current_view = self.tab_widget.currentWidget()
        return current_view.scene() if current_view else None
    
    def get_current_view(self):
        """Get the currently active view."""
        return self.tab_widget.currentWidget()
        
    def create_menus(self):
        """Create the menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("📁 &File")
        
        new_action = QAction("📄 &New", self)
        new_action.setShortcut(QKeySequence.StandardKey.New)
        new_action.triggered.connect(self.new_diagram)
        file_menu.addAction(new_action)
        
        file_menu.addSeparator()
        
        open_action = QAction("📂 &Open...", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)
        
        save_action = QAction("💾 &Save", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)
        
        save_as_action = QAction("💾 Save &As...", self)
        save_as_action.setShortcut(QKeySequence.StandardKey.SaveAs)
        save_as_action.triggered.connect(self.save_file_as)
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("🚪 E&xit", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu("✏️ &Edit")
        
        # Get the global undo stack
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance()
        undo_stack = app.undo_stack
        
        # Add undo action
        undo_action = undo_stack.createUndoAction(self, "↶ &Undo")
        undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        edit_menu.addAction(undo_action)
        
        # Add redo action
        redo_action = undo_stack.createRedoAction(self, "↷ &Redo")
        redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        edit_menu.addAction(redo_action)
        
        # Add separator
        edit_menu.addSeparator()
        
        # Add delete action
        delete_action = QAction("🗑️ &Delete", self)
        delete_action.setShortcut(QKeySequence.StandardKey.Delete)
        delete_action.triggered.connect(self.delete_selected_items)
        edit_menu.addAction(delete_action)
        
        # Diagram menu
        diagram_menu = menubar.addMenu("📊 &Diagram")
        
        new_diagram_action = QAction("➕ &New Diagram", self)
        new_diagram_action.setShortcut("Ctrl+Shift+N")
        new_diagram_action.triggered.connect(self.create_new_diagram)
        diagram_menu.addAction(new_diagram_action)
        
        diagram_menu.addSeparator()
        
        settings_action = QAction("⚙️ &Settings...", self)
        settings_action.setShortcut("Ctrl+,")
        # Add gear icon if available
        try:
            # Try to use a more appropriate settings-related icon
            settings_action.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_ComputerIcon))
        except:
            pass  # If icon not available, just use text
        settings_action.triggered.connect(self.show_diagram_settings)
        diagram_menu.addAction(settings_action)
        
        # View menu
        view_menu = menubar.addMenu("👁️ &View")
        
        zoom_in_action = QAction("🔍+ Zoom &In", self)
        zoom_in_action.setShortcut(QKeySequence.StandardKey.ZoomIn)
        zoom_in_action.triggered.connect(self.zoom_in)
        view_menu.addAction(zoom_in_action)
        
        zoom_out_action = QAction("🔍- Zoom &Out", self)
        zoom_out_action.setShortcut(QKeySequence.StandardKey.ZoomOut)
        zoom_out_action.triggered.connect(self.zoom_out)
        view_menu.addAction(zoom_out_action)
        
        reset_zoom_action = QAction("🎯 &Reset Zoom", self)
        reset_zoom_action.setShortcut("Ctrl+0")
        reset_zoom_action.triggered.connect(self.reset_zoom)
        view_menu.addAction(reset_zoom_action)
        
        view_menu.addSeparator()
        
        fit_all_action = QAction("📐 &Fit All", self)
        fit_all_action.setShortcut("Ctrl+F")
        fit_all_action.triggered.connect(self.fit_in_view_all)
        view_menu.addAction(fit_all_action)
        
        # Proof menu
        proof_menu = menubar.addMenu("🔍 &Proof")
        
        # Toggle for proof step buttons - default unchecked
        self.proof_buttons_action = QAction("🔘 Proof Step &Buttons", self)
        self.proof_buttons_action.setCheckable(True)
        self.proof_buttons_action.setChecked(False)  # Default unchecked
        self.proof_buttons_action.triggered.connect(self.toggle_proof_buttons)
        proof_menu.addAction(self.proof_buttons_action)
        
        # Help menu
        help_menu = menubar.addMenu("❓ &Help")
        
        about_action = QAction("ℹ️ &About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def create_toolbar(self):
        """Create the toolbar."""
        toolbar = QToolBar("🔧 Main Toolbar", self)
        toolbar.setObjectName("MainToolbar")  # Set object name to avoid warning
        self.addToolBar(toolbar)
        
        # New diagram button
        new_btn = QPushButton("📄 New", self)
        new_btn.clicked.connect(self.create_new_diagram)
        toolbar.addWidget(new_btn)
        
        toolbar.addSeparator()
        
        # Zoom buttons
        zoom_in_btn = QPushButton("🔍+ Zoom In", self)
        zoom_in_btn.clicked.connect(self.zoom_in)
        toolbar.addWidget(zoom_in_btn)
        
        zoom_out_btn = QPushButton("🔍- Zoom Out", self)
        zoom_out_btn.clicked.connect(self.zoom_out)
        toolbar.addWidget(zoom_out_btn)
        
        reset_zoom_btn = QPushButton("🎯 Reset Zoom", self)
        reset_zoom_btn.clicked.connect(self.reset_zoom)
        toolbar.addWidget(reset_zoom_btn)
        
        toolbar.addSeparator()
        
        # Fit all button
        fit_all_btn = QPushButton("📐 Fit All", self)
        fit_all_btn.clicked.connect(self.fit_in_view_all)
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
        self.status_bar.showMessage("✅ Ready. Double-click canvas for objects 📦, objects for arrows ➡️. Right-click for options and labels.")
        
    def new_diagram(self):
        """Create a new diagram (for backward compatibility)."""
        self.create_new_diagram()
        
    def reset_zoom(self):
        """Reset zoom for current view."""
        current_view = self.get_current_view()
        if current_view:
            current_view.reset_zoom()
            self.update_zoom_label()
        
    def fit_in_view_all(self):
        """Fit all items in current view."""
        current_view = self.get_current_view()
        if current_view:
            current_view.fit_in_view_all()
            self.update_zoom_label()
        
    def zoom_in(self):
        """Zoom in the view."""
        current_view = self.get_current_view()
        if current_view:
            current_zoom = current_view.get_zoom_level()
            if current_zoom < 5.0:
                current_view.scale(1.15, 1.15)
                self.update_zoom_label()
            
    def zoom_out(self):
        """Zoom out the view."""
        current_view = self.get_current_view()
        if current_view:
            current_zoom = current_view.get_zoom_level()
            if current_zoom > 0.1:
                current_view.scale(1/1.15, 1/1.15)
                self.update_zoom_label()
    
    def toggle_proof_buttons(self):
        """Toggle the proof step buttons overlay on/off."""
        is_enabled = self.proof_buttons_action.isChecked()
        
        # Apply to current view
        current_view = self.get_current_view()
        if current_view:
            current_view.set_proof_buttons_enabled(is_enabled)
        
        # Apply to all views
        for i in range(self.tab_widget.count()):
            widget = self.tab_widget.widget(i)
            if hasattr(widget, 'view'):
                widget.view.set_proof_buttons_enabled(is_enabled)
            
    def update_zoom_label(self):
        """Update the zoom level display in status bar."""
        current_view = self.get_current_view()
        if current_view:
            zoom_percent = int(current_view.get_zoom_level() * 100)
            self.zoom_label.setText(f"Zoom: {zoom_percent}%")
        
    def on_object_added(self, obj):
        """Handle when an object is added to the scene."""
        current_scene = self.get_current_scene()
        if current_scene:
            object_count = len([item for item in current_scene.items() 
                               if hasattr(item, 'get_text')])
            self.status_bar.showMessage(f"📦 Object added. Total objects: {object_count}")
    
    def show_diagram_settings(self):
        """Show the diagram settings dialog."""
        from dialog.diagram_settings_dialog import DiagramSettingsDialog
        
        dialog = DiagramSettingsDialog(self)
        dialog.set_settings(self.diagram_settings)
        
        if dialog.exec() == dialog.DialogCode.Accepted:
            # Update settings
            self.diagram_settings = dialog.get_settings()
            
            # Apply settings to current scene/view
            self.apply_settings_to_current_diagram()
            
            # Update status
            self.status_bar.showMessage("⚙️ Diagram settings updated.")
    
    def apply_settings_to_current_diagram(self):
        """Apply current settings to the active diagram."""
        current_scene = self.get_current_scene()
        current_view = self.get_current_view()
        
        if not current_scene or not current_view:
            return
        
        # Handle grid spacing changes with position scaling
        old_grid_spacing = getattr(current_scene, '_grid_size', 150)
        new_grid_spacing = self.diagram_settings['grid_spacing']
        
        if old_grid_spacing != new_grid_spacing:
            # Calculate scale factor and apply scaling
            scale_factor = new_grid_spacing / old_grid_spacing if old_grid_spacing > 0 else 1.0
            if abs(scale_factor - 1.0) > 0.01:  # Only scale if change is significant
                self._scale_scene_positions(current_scene, scale_factor)
        
        # Apply grid settings
        if hasattr(current_scene, '_grid_size'):
            current_scene._grid_size = new_grid_spacing
        if hasattr(current_scene, '_grid_enabled'):
            current_scene._grid_enabled = self.diagram_settings['show_grid']
        
        # Apply background color
        current_scene.setBackgroundBrush(self.diagram_settings['bg_color'])
        
        # Update the scene to reflect changes
        current_scene.update()
        current_view.update()
        
        # TODO: Apply other settings to existing objects and arrows
        # This would require iterating through scene items and updating their properties
        
    def apply_settings_to_new_diagram(self, scene, view):
        """Apply current settings to a newly created diagram."""
        if hasattr(scene, '_grid_size'):
            scene._grid_size = self.diagram_settings['grid_spacing']
        if hasattr(scene, '_grid_enabled'):
            scene._grid_enabled = self.diagram_settings['show_grid']
        
        # Apply background color
        scene.setBackgroundBrush(self.diagram_settings['bg_color'])
        
    def check_and_adjust_grid_spacing(self, modified_node=None):
        """Check arrow lengths and adjust grid spacing if auto-spacing is enabled."""
        if not self.diagram_settings.get('auto_grid_spacing', False):
            return  # Auto-spacing is disabled
        
        current_scene = self.get_current_scene()
        if not current_scene:
            return
        
        # Collect all arrows in the scene
        arrows = []
        for item in current_scene.items():
            if hasattr(item, 'get_source') and hasattr(item, 'get_target') and hasattr(item, 'get_length'):
                arrows.append(item)
        
        if not arrows:
            return  # No arrows to check
        
        # Calculate arrow lengths
        arrow_lengths = [arrow.get_length() for arrow in arrows]
        current_grid_spacing = self.diagram_settings['grid_spacing']
        
        # Check if any arrow is 50 or less - double the grid spacing
        min_length = min(arrow_lengths)
        if min_length <= 50:
            new_spacing = min(current_grid_spacing * 2, 500)  # Cap at 500px
            if new_spacing != current_grid_spacing:
                self._update_grid_spacing(new_spacing)
                self.status_bar.showMessage(f"📏⬆️ Auto-doubled grid spacing to {new_spacing}px (shortest arrow: {min_length:.1f}px)")
                return
        
        # Check if all arrows are 80% or more of grid spacing - half the spacing
        threshold_length = current_grid_spacing * 0.8
        if all(length >= threshold_length for length in arrow_lengths):
            new_spacing = max(current_grid_spacing // 2, 50)  # Floor at 50px
            if new_spacing != current_grid_spacing:
                self._update_grid_spacing(new_spacing)
                self.status_bar.showMessage(f"📏⬇️ Auto-halved grid spacing to {new_spacing}px (all arrows ≥ {threshold_length:.1f}px)")
    
    def _update_grid_spacing(self, new_spacing):
        """Update grid spacing setting and apply to current diagram."""
        current_scene = self.get_current_scene()
        if not current_scene:
            return
            
        # Get the current grid spacing for scaling calculation
        old_spacing = self.diagram_settings['grid_spacing']
        scale_factor = new_spacing / old_spacing if old_spacing > 0 else 1.0
        
        # Update the setting
        self.diagram_settings['grid_spacing'] = new_spacing
        
        # Scale all object and arrow positions if there's a significant change
        if abs(scale_factor - 1.0) > 0.01:  # Only scale if change is significant
            self._scale_scene_positions(current_scene, scale_factor)
        
        # Apply to current scene
        if hasattr(current_scene, '_grid_size'):
            current_scene._grid_size = new_spacing
            current_scene.update()
    
    def _scale_scene_positions(self, scene, scale_factor):
        """Scale all object and arrow positions in the scene by the given factor."""
        if not scene:
            return
            
        # Scale all objects
        for item in scene.items():
            if hasattr(item, 'pos') and hasattr(item, 'setPos'):
                # Scale object positions
                current_pos = item.pos()
                new_pos = current_pos * scale_factor
                item.setPos(new_pos)
                
                # If it's an arrow, also update its internal position tracking
                if hasattr(item, 'update_position'):
                    item.update_position()
        
        # Update scene rect to accommodate scaled positions
        scene.setSceneRect(scene.itemsBoundingRect())
        
        # Update the scene
        scene.update()
        
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
        current_scene = self.get_current_scene()
        if not current_scene:
            return
            
        # Get selected items from the scene
        selected_items = current_scene.selectedItems()
        
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
        from core.undo_commands import DeleteItems
        from PyQt6.QtWidgets import QApplication
        
        command = DeleteItems(current_scene, deletable_items)
        app = QApplication.instance()
        app.undo_stack.push(command)
        
        # Update status bar
        if len(deletable_items) == 1:
            item = deletable_items[0]
            if hasattr(item, 'get_text'):
                item_name = item.get_text()
                item_type = "Object" if hasattr(item, 'boundingRect') and item.type() == 65537 else "Arrow"
                self.status_bar.showMessage(f"🗑️ Deleted {item_type} '{item_name}'.")
            else:
                self.status_bar.showMessage("🗑️ Deleted item.")
        else:
            self.status_bar.showMessage(f"🗑️ Deleted {len(deletable_items)} items.")
        
    def closeEvent(self, event):
        """Handle application close event."""
        # Save window state and application data before closing
        self.save_session_data()
        
        # Could add save confirmation here if needed
        event.accept()
    
    def save_session_data(self):
        """Save current session data including window state and diagrams."""
        try:
            # Save window geometry and state
            self.session_manager.save_window_state(self)
            
            # Serialize window data
            window_data = self.session_manager.serialize_window_data(self)
            
            # Save application data (this window only for now)
            self.session_manager.save_application_data([window_data])
            
        except Exception as e:
            print(f"Error saving session data: {e}")
            import traceback
            traceback.print_exc()
    
    def restore_session_data(self):
        """Restore session data including window state and diagrams."""
        try:
            # Restore window geometry and state
            if self.session_manager.restore_window_state(self):
                print("Window state restored successfully")
            
            # Load application data
            session_data = self.session_manager.load_application_data()
            if session_data and 'windows' in session_data:
                windows_data = session_data['windows']
                
                if windows_data:
                    # Restore the first window's data
                    window_data = windows_data[0]
                    self.restore_window_diagrams(window_data)
                    
                    # Restore diagram settings
                    if 'settings' in window_data:
                        self.diagram_settings.update(window_data['settings'])
        
        except Exception as e:
            print(f"Error restoring session data: {e}")
            import traceback
            traceback.print_exc()
    
    def restore_window_diagrams(self, window_data: dict):
        """Restore diagrams for this window."""
        try:
            diagrams_data = window_data.get('diagrams', [])
            
            # Process the diagram list (handles both strings and dicts)
            processed_diagrams = self.session_manager.process_diagram_list(diagrams_data)
            
            # Clear existing tabs
            while self.tab_widget.count() > 0:
                self.tab_widget.removeTab(0)
            
            active_tab_index = -1
            
            # Restore each diagram
            for i, diagram_info in enumerate(processed_diagrams):
                diagram_name = diagram_info.get('name', f'Diagram {i+1}')
                diagram_data = diagram_info.get('data', {})
                is_active = diagram_info.get('active', False)
                
                # Create new diagram tab
                scene = DiagramScene(self)
                view = DiagramView(scene, self)
                
                # Restore the diagram content
                if self.session_manager.restore_diagram_scene(scene, diagram_data):
                    # Add tab
                    tab_index = self.tab_widget.addTab(view, diagram_name)
                    
                    if is_active:
                        active_tab_index = tab_index
                else:
                    print(f"Failed to restore diagram: {diagram_name}")
            
            # Set active tab
            if active_tab_index >= 0:
                self.tab_widget.setCurrentIndex(active_tab_index)
            
            # If no diagrams were restored, create a default one
            if self.tab_widget.count() == 0:
                self.create_new_diagram()
        
        except Exception as e:
            print(f"Error restoring window diagrams: {e}")
            import traceback
            traceback.print_exc()
            
            # Fallback: create a new diagram
            self.create_new_diagram()
    
    def resizeEvent(self, event):
        """Handle window resize events to save geometry."""
        super().resizeEvent(event)
        self._schedule_geometry_save()
    
    def moveEvent(self, event):
        """Handle window move events to save geometry."""
        super().moveEvent(event)
        self._schedule_geometry_save()
    
    def changeEvent(self, event):
        """Handle window state changes."""
        super().changeEvent(event)
        if event.type() in [event.Type.WindowStateChange]:
            self._schedule_geometry_save()
    
    def _schedule_geometry_save(self):
        """Schedule geometry save to avoid too frequent saves."""
        from PyQt6.QtCore import QTimer
        
        if self._geometry_timer is not None:
            self._geometry_timer.stop()
        
        self._geometry_timer = QTimer()
        self._geometry_timer.setSingleShot(True)
        self._geometry_timer.timeout.connect(self._save_geometry)
        self._geometry_timer.start(1000)  # Save after 1 second of inactivity
    
    def _save_geometry(self):
        """Save window geometry to QSettings."""
        try:
            self.session_manager.save_window_state(self)
        except Exception as e:
            print(f"Error saving geometry: {e}")
    
    # File handling methods
    def open_file(self):
        """Open an app data JSON file."""
        if self.is_modified and not self._confirm_discard_changes():
            return
            
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open App Data File",
            "",
            "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            self._load_file(file_path)
    
    def save_file(self):
        """Save the current app data to file."""
        if self.current_file:
            self._save_to_file(self.current_file)
        else:
            self.save_file_as()
    
    def save_file_as(self):
        """Save the current app data to a new file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save App Data File",
            "",
            "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            if not file_path.endswith('.json'):
                file_path += '.json'
            self._save_to_file(file_path)
    
    def new_file(self):
        """Create a new file (clear current data)."""
        if self.is_modified and not self._confirm_discard_changes():
            return
            
        # Clear all tabs
        while self.tab_widget.count() > 0:
            self.tab_widget.removeTab(0)
        
        # Clear undo stack
        app = QApplication.instance()
        if hasattr(app, 'clear_undo_stack'):
            app.clear_undo_stack()
        
        # Create initial diagram
        self.new_diagram()
        
        # Reset file state
        self.current_file = None
        self.is_modified = False
        self._update_window_title()
    
    def _load_file(self, file_path: str):
        """Load app data from the specified file."""
        try:
            data = self.session_manager.load_application_data(file_path)
            if not data:
                QMessageBox.warning(self, "Error", f"Could not load file: {file_path}")
                return
            
            # Clear current content
            while self.tab_widget.count() > 0:
                self.tab_widget.removeTab(0)
            
            # Restore windows/tabs data
            if 'windows' in data:
                for window_data in data['windows']:
                    self._restore_window_data(window_data)
            
            # Restore undo stack if available
            if 'undo_stack' in data:
                app = QApplication.instance()
                if hasattr(app, 'deserialize_undo_stack'):
                    app.deserialize_undo_stack(data['undo_stack'])
            
            self.current_file = file_path
            self.is_modified = False
            self._update_window_title()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load file: {e}")
    
    def _save_to_file(self, file_path: str):
        """Save current app data to the specified file."""
        try:
            # Collect all window data
            windows_data = self._collect_windows_data()
            
            # Get undo stack data
            app = QApplication.instance()
            undo_stack_data = None
            if hasattr(app, 'serialize_undo_stack'):
                undo_stack_data = app.serialize_undo_stack()
            
            # Create session data directly as JSON
            import json
            from datetime import datetime
            
            session_data = {
                "version": "1.0", 
                "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
                "windows": windows_data,
                "undo_stack": undo_stack_data or {}
            }
            
            # Save to file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)
            
            self.current_file = file_path
            self.is_modified = False
            self._update_window_title()
            
            QMessageBox.information(self, "Success", f"File saved: {file_path}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save file: {e}")
    
    def _collect_windows_data(self):
        """Collect data from all open windows/tabs."""
        windows_data = []
        
        for i in range(self.tab_widget.count()):
            widget = self.tab_widget.widget(i)
            tab_name = self.tab_widget.tabText(i)
            
            if isinstance(widget, DiagramView):
                scene = widget.scene()
                if hasattr(scene, 'serialize'):
                    scene_data = scene.serialize()
                else:
                    scene_data = self.session_manager.serialize_diagram_scene(scene)
                
                windows_data.append({
                    'tab_name': tab_name,
                    'scene_data': scene_data
                })
        
        return windows_data
    
    def _restore_window_data(self, window_data):
        """Restore a window/tab from saved data."""
        if 'scene_data' not in window_data:
            return
            
        tab_name = window_data.get('tab_name', 'Restored Diagram')
        scene_data = window_data['scene_data']
        
        # Create new diagram tab
        scene = DiagramScene()
        view = DiagramView(scene)
        
        # Restore scene data
        if hasattr(scene, 'deserialize'):
            scene.deserialize(scene_data)
        else:
            self.session_manager.restore_diagram_scene(scene, scene_data)
        
        # Add tab
        self.tab_widget.addTab(view, tab_name)
    
    def _confirm_discard_changes(self):
        """Ask user to confirm discarding unsaved changes."""
        reply = QMessageBox.question(
            self,
            "Unsaved Changes",
            "You have unsaved changes. Do you want to discard them?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        return reply == QMessageBox.StandardButton.Yes
    
    def _update_window_title(self):
        """Update the window title to reflect current file."""
        title = "Pythom - DAG Diagram Editor"
        if self.current_file:
            filename = os.path.basename(self.current_file)
            title = f"{filename} - {title}"
            if self.is_modified:
                title = f"* {title}"
        elif self.is_modified:
            title = f"* {title}"
        
        self.setWindowTitle(title)
    
    def mark_modified(self):
        """Mark the document as modified."""
        if not self.is_modified:
            self.is_modified = True
            self._update_window_title()
