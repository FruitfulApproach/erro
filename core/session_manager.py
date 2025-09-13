"""
Session persistence manager for ArrowCatcher application.
Handles window state, geometry, and application data serialization.
"""
import json
import pickle
import os
from datetime import datetime
from typing import Dict, List, Any, Union, Optional
from pathlib import Path

from PyQt6.QtCore import QSettings, QByteArray
from PyQt6.QtWidgets import QMainWindow, QApplication


class SessionManager:
    """Manages session persistence using QSettings and JSON/pickle serialization."""
    
    def __init__(self):
        # Initialize QSettings with company and product names
        self.settings = QSettings("ArrowCatcher", "ArrowCatcher")
        
        # Create data directory for session files
        self.data_dir = Path.home() / ".arrowcatcher" / "sessions"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Current session file
        self.current_session_file = None
    
    def save_window_state(self, window: QMainWindow, window_id: str = "main"):
        """Save window geometry, position, and state to QSettings."""
        self.settings.beginGroup(f"window_{window_id}")
        
        # Save geometry and position
        self.settings.setValue("geometry", window.saveGeometry())
        self.settings.setValue("windowState", window.saveState())
        self.settings.setValue("isMaximized", window.isMaximized())
        self.settings.setValue("isMinimized", window.isMinimized())
        
        # Save position explicitly for non-maximized windows
        if not window.isMaximized():
            self.settings.setValue("position", window.pos())
            self.settings.setValue("size", window.size())
        
        self.settings.endGroup()
        self.settings.sync()
    
    def restore_window_state(self, window: QMainWindow, window_id: str = "main") -> bool:
        """Restore window geometry, position, and state from QSettings."""
        self.settings.beginGroup(f"window_{window_id}")
        
        success = False
        
        # Restore geometry if available
        geometry = self.settings.value("geometry")
        if geometry:
            window.restoreGeometry(geometry)
            success = True
        
        # Restore window state (toolbars, docks, etc.)
        window_state = self.settings.value("windowState")
        if window_state:
            window.restoreState(window_state)
            success = True
        
        # Handle maximized state
        is_maximized = self.settings.value("isMaximized", False, bool)
        if is_maximized:
            window.showMaximized()
            success = True
        
        # Handle minimized state
        is_minimized = self.settings.value("isMinimized", False, bool)
        if is_minimized:
            window.showMinimized()
            success = True
        
        self.settings.endGroup()
        return success
    
    def save_application_data(self, windows_data: List[Dict[str, Any]], undo_stack_data: Dict[str, Any] = None) -> str:
        """Save application data including undo stack to JSON file and update QSettings."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_file = self.data_dir / f"session_{timestamp}.json"
        
        try:
            # Get undo stack data from the application if not provided
            if undo_stack_data is None:
                app = QApplication.instance()
                if hasattr(app, 'serialize_undo_stack'):
                    undo_stack_data = app.serialize_undo_stack()
            
            # Prepare session data
            session_data = {
                "version": "1.0",
                "timestamp": timestamp,
                "windows": windows_data,
                "undo_stack": undo_stack_data or {}
            }
            
            # Save as JSON (preferred for readability and portability)
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)
            
            # Update QSettings with latest session file
            self.settings.setValue("lastSessionFile", str(session_file))
            self.settings.sync()
            
            self.current_session_file = session_file
            return str(session_file)
            
        except Exception as e:
            print(f"Error saving application data: {e}")
            
            # Fallback to pickle if JSON fails
            try:
                pickle_file = session_file.with_suffix('.pkl')
                with open(pickle_file, 'wb') as f:
                    pickle.dump(session_data, f)
                
                self.settings.setValue("lastSessionFile", str(pickle_file))
                self.settings.sync()
                
                self.current_session_file = pickle_file
                return str(pickle_file)
                
            except Exception as pickle_error:
                print(f"Error saving with pickle: {pickle_error}")
                return ""
    
    def load_application_data(self, session_file: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Load application data from JSON/pickle file."""
        if not session_file:
            # Get last session file from QSettings
            session_file = self.settings.value("lastSessionFile", "")
        
        if not session_file or not os.path.exists(session_file):
            return None
        
        try:
            # Try loading as JSON first
            if session_file.endswith('.json'):
                with open(session_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            
            # Try loading as pickle
            elif session_file.endswith('.pkl'):
                with open(session_file, 'rb') as f:
                    return pickle.load(f)
            
            # Try to auto-detect format
            else:
                # Try JSON first
                try:
                    with open(session_file, 'r', encoding='utf-8') as f:
                        return json.load(f)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    # Fallback to pickle
                    with open(session_file, 'rb') as f:
                        return pickle.load(f)
        
        except Exception as e:
            print(f"Error loading application data from {session_file}: {e}")
            return None
    
    def serialize_diagram_scene(self, scene) -> Dict[str, Any]:
        """Serialize a DiagramScene to a dictionary."""
        try:
            # Get all items in the scene
            objects = []
            arrows = []
            
            for item in scene.items():
                # Check if it's an object node
                if hasattr(item, 'get_text') and not hasattr(item, 'get_source'):
                    objects.append({
                        'id': id(item),
                        'text': item.get_text(),
                        'position': {'x': item.pos().x(), 'y': item.pos().y()},
                        'size': {'width': item.boundingRect().width(), 
                                'height': item.boundingRect().height()}
                    })
                
                # Check if it's an arrow
                elif hasattr(item, 'get_source') and hasattr(item, 'get_target'):
                    # For arrows, use base name if available, otherwise fall back to get_text
                    if hasattr(item, 'get_base_name'):
                        text = item.get_base_name()
                    elif hasattr(item, 'get_text'):
                        text = item.get_text()
                    else:
                        text = ""
                    
                    arrows.append({
                        'id': id(item),
                        'source_id': id(item.get_source()),
                        'target_id': id(item.get_target()),
                        'text': text,
                        'color': item.pen().color().name() if hasattr(item, 'pen') else "#000000",
                        'is_inclusion': getattr(item, '_is_inclusion', False)  # Save inclusion property
                    })
            
            return {
                'objects': objects,
                'arrows': arrows,
                'scene_rect': {
                    'x': scene.sceneRect().x(),
                    'y': scene.sceneRect().y(),
                    'width': scene.sceneRect().width(),
                    'height': scene.sceneRect().height()
                }
            }
        
        except Exception as e:
            print(f"Error serializing diagram scene: {e}")
            return {}
    
    def save_diagram_scene_to_file(self, scene, filename: str) -> bool:
        """Save a DiagramScene to a separate JSON file."""
        try:
            diagram_data = self.serialize_diagram_scene(scene)
            
            # Ensure the filename has .json extension
            if not filename.endswith('.json'):
                filename += '.json'
            
            filepath = self.data_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(diagram_data, f, indent=2, ensure_ascii=False)
            
            return True
        
        except Exception as e:
            print(f"Error saving diagram scene to file {filename}: {e}")
            return False
    
    def load_diagram_scene_from_file(self, filename: str) -> Optional[Dict[str, Any]]:
        """Load a DiagramScene from a JSON file."""
        try:
            # Handle both absolute and relative paths
            if os.path.isabs(filename):
                filepath = Path(filename)
            else:
                filepath = self.data_dir / filename
            
            # Ensure .json extension
            if not filepath.suffix:
                filepath = filepath.with_suffix('.json')
            
            if not filepath.exists():
                return None
            
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        except Exception as e:
            print(f"Error loading diagram scene from file {filename}: {e}")
            return None
    
    def serialize_window_data(self, main_window) -> Dict[str, Any]:
        """Serialize a MainWindow's data including tabs and diagrams."""
        try:
            tab_widget = main_window.tab_widget
            diagrams = []
            
            for i in range(tab_widget.count()):
                tab_name = tab_widget.tabText(i)
                widget = tab_widget.widget(i)
                
                if hasattr(widget, 'scene'):
                    scene = widget.scene()
                    
                    # Option 1: Embed diagram data directly (for small diagrams)
                    scene_data = self.serialize_diagram_scene(scene)
                    
                    # Option 2: Save to separate file (for large diagrams or external sharing)
                    # Uncomment the following lines to use file references instead:
                    # diagram_filename = f"diagram_{tab_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    # if self.save_diagram_scene_to_file(scene, diagram_filename):
                    #     diagrams.append(diagram_filename)  # Add as string reference
                    # else:
                    #     diagrams.append(scene_data)  # Fallback to embedded data
                    
                    # For now, we'll embed the data directly
                    diagrams.append({
                        'name': tab_name,
                        'data': scene_data,
                        'active': i == tab_widget.currentIndex()
                    })
            
            return {
                'window_id': str(id(main_window)),
                'diagrams': diagrams,
                'settings': main_window.diagram_settings if hasattr(main_window, 'diagram_settings') else {}
            }
        
        except Exception as e:
            print(f"Error serializing window data: {e}")
            return {}
    
    def cleanup_old_sessions(self, keep_count: int = 10):
        """Clean up old session files, keeping only the most recent ones."""
        try:
            session_files = list(self.data_dir.glob("session_*.json")) + \
                           list(self.data_dir.glob("session_*.pkl"))
            
            # Sort by modification time, newest first
            session_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
            
            # Remove old files
            for old_file in session_files[keep_count:]:
                old_file.unlink()
                
        except Exception as e:
            print(f"Error cleaning up old sessions: {e}")
    
    def get_available_sessions(self) -> List[Dict[str, Any]]:
        """Get list of available session files with metadata."""
        sessions = []
        
        try:
            session_files = list(self.data_dir.glob("session_*.json")) + \
                           list(self.data_dir.glob("session_*.pkl"))
            
            for session_file in session_files:
                stat = session_file.stat()
                sessions.append({
                    'filename': str(session_file),
                    'name': session_file.stem,
                    'modified': datetime.fromtimestamp(stat.st_mtime),
                    'size': stat.st_size
                })
            
            # Sort by modification time, newest first
            sessions.sort(key=lambda s: s['modified'], reverse=True)
            
        except Exception as e:
            print(f"Error getting available sessions: {e}")
        
    def restore_diagram_scene(self, scene, diagram_data: Dict[str, Any]):
        """Restore a DiagramScene from serialized data."""
        try:
            from widget.object_node import Object
            from widget.arrow import Arrow
            
            # Clear existing scene
            scene.clear()
            
            # Restore scene rect
            if 'scene_rect' in diagram_data:
                rect_data = diagram_data['scene_rect']
                from PyQt6.QtCore import QRectF
                scene.setSceneRect(QRectF(
                    rect_data['x'], rect_data['y'],
                    rect_data['width'], rect_data['height']
                ))
            
            # Create a mapping of old IDs to new objects for arrow restoration
            id_mapping = {}
            
            # Restore objects first
            objects_data = diagram_data.get('objects', [])
            for obj_data in objects_data:
                # Create object node
                obj = Object(obj_data['text'])
                
                # Set position
                pos_data = obj_data['position']
                obj.setPos(pos_data['x'], pos_data['y'])
                
                # Add to scene
                scene.addItem(obj)
                
                # Map old ID to new object
                id_mapping[obj_data['id']] = obj
            
            # Restore arrows
            arrows_data = diagram_data.get('arrows', [])
            for arrow_data in arrows_data:
                source_id = arrow_data['source_id']
                target_id = arrow_data['target_id']
                
                # Find source and target objects
                source = id_mapping.get(source_id)
                target = id_mapping.get(target_id)
                
                if source and target:
                    # Create arrow
                    arrow = Arrow(source, target)
                    
                    # Set text if available
                    if 'text' in arrow_data and arrow_data['text']:
                        # Use set_base_name if available, otherwise fall back to set_text
                        if hasattr(arrow, 'set_base_name'):
                            arrow.set_base_name(arrow_data['text'])
                        else:
                            arrow.set_text(arrow_data['text'])
                    
                    # Set color if available
                    if 'color' in arrow_data:
                        from PyQt6.QtGui import QColor, QPen
                        color = QColor(arrow_data['color'])
                        pen = QPen(color, 2)  # Use default width
                        arrow._pen = pen  # Set private attribute directly
                    
                    # Restore inclusion property if available
                    if 'is_inclusion' in arrow_data:
                        arrow._is_inclusion = arrow_data['is_inclusion']
                    
                    # Add to scene
                    scene.addItem(arrow)
            
            return True
            
        except Exception as e:
            print(f"Error restoring diagram scene: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def process_diagram_list(self, diagrams_list: List[Union[str, Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Process a list of diagrams that can be either file paths (str) or embedded data (dict)."""
        processed_diagrams = []
        
        for diagram_item in diagrams_list:
            if isinstance(diagram_item, str):
                # It's a file path, load from file
                diagram_data = self.load_diagram_scene_from_file(diagram_item)
                if diagram_data:
                    processed_diagrams.append({
                        'name': Path(diagram_item).stem,
                        'data': diagram_data,
                        'source_file': diagram_item,
                        'active': False  # Will be set by caller if needed
                    })
                else:
                    print(f"Warning: Could not load diagram from file: {diagram_item}")
            
            elif isinstance(diagram_item, dict):
                # It's embedded data
                if 'data' in diagram_item:
                    # New format with metadata
                    processed_diagrams.append(diagram_item)
                else:
                    # Legacy format - assume the dict is the diagram data itself
                    processed_diagrams.append({
                        'name': f"Diagram {len(processed_diagrams) + 1}",
                        'data': diagram_item,
                        'active': False
                    })
        
        return processed_diagrams
