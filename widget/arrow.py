"""
Arrow node for connecting objects in DAG diagrams.
"""
from PyQt6.QtWidgets import QGraphicsItem, QMenu
from PyQt6.QtCore import QRectF, QPointF, Qt, pyqtSignal
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QPolygonF, QFont, QAction
import math
from .node import Node


class Arrow(Node):
    """Arrow node for connecting objects in the DAG."""
    
    # Signal emitted when arrow text changes
    text_changed = pyqtSignal(str)  # emits the new text
    
    def __init__(self, start_node=None, end_node=None, text="a", parent=None):
        super().__init__(parent)
        self._start_node = start_node
        self._end_node = end_node
        self._start_point = QPointF(0, 0)
        self._end_point = QPointF(100, 0)
        
        # Self-loop properties
        self._is_self_loop = False
        self._loop_center = QPointF(0, 0)
        self._loop_radius = 50
        
        # Parallel arrow properties
        self._is_curved = False
        self._curve_offset = 0
        self._control_point_1 = QPointF(0, 0)
        self._control_point_2 = QPointF(0, 0)
        
        # Arrow text properties
        self._text = text
        self._font = QFont("Arial", 11)
        self._label_visible = True  # Track automatic label visibility
        self._label_manually_hidden = False  # Manual label hiding flag
        
        # Arrow-specific styling
        self._pen = QPen(QColor(100, 100, 100), 2)
        self._brush = QBrush(QColor(100, 100, 100))
        self._arrow_head_size = 7
        
        # "There Exists" property for dashed line style
        self._there_exists = False
        self._solid_pen = self._pen  # Store original solid pen
        
        # Arrow style properties
        self._is_inclusion = False      # HookTail
        self._is_monomorphism = False   # VeeTail  
        self._is_epimorphism = False    # TwoHead
        self._is_isomorphism = False    # SimilarityArrow (~)
        self._is_general = True         # GeneralArrow (default)
        
        # Kernel arrow flag - kernel arrows are automatically inclusions
        self._is_kernel_arrow = False
        
        # Highlighting for cycle detection
        self._highlight_color = None
        self._original_pen = self._pen
        self._original_brush = self._brush
        
        # Arrow is not movable by default (controlled by connected nodes)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
        
        # Set arrow to appear behind objects
        self.setZValue(-1)
        
        # Connect to node movement signals if nodes are provided
        if self._start_node:
            self._start_node.node_moved.connect(self.update_position)
            # Connect to name changes to update label visibility
            if hasattr(self._start_node, 'name_changed'):
                self._start_node.name_changed.connect(self._update_label_visibility)
        if self._end_node:
            self._end_node.node_moved.connect(self.update_position)
            # Connect to name changes to update label visibility  
            if hasattr(self._end_node, 'name_changed'):
                self._end_node.name_changed.connect(self._update_label_visibility)
            
        # Signal connections for text updates (to be managed by proof steps)
        self._signal_connections = []  # List of (sender, signal, slot) tuples
            
        self.update_position()
        
        # Initialize label visibility based on current conditions
        self._update_label_visibility()
        
    def _signal_setup(self):
        """Set up signal connections based on arrow text content."""
        self._signal_cleanup()  # Clean up any existing connections
        
        # Check for identity arrows (1_X pattern)
        import re
        identity_matches = re.findall(r'1_([^∘\s]+)', self._text)
        for node_name in identity_matches:
            # Find the node with this name in the scene
            if self.scene():
                for item in self.scene().items():
                    if (hasattr(item, 'get_text') and 
                        hasattr(item, 'name_changed') and 
                        item.get_text() == node_name):
                        # Connect this node's name_changed to our text update
                        item.name_changed.connect(self._update_identity_text)
                        self._signal_connections.append((item, item.name_changed, self._update_identity_text))
        
        # Check for composition arrows (containing ∘ symbol)
        if '∘' in self._text:
            # Find all component arrow names in the composition
            components = [comp.strip() for comp in self._text.split('∘')]
            for comp_name in components:
                if comp_name and not comp_name.startswith('1_'):  # Skip identities
                    # Find arrows with this text in the scene
                    if self.scene():
                        for item in self.scene().items():
                            if (hasattr(item, 'get_text') and 
                                hasattr(item, 'text_changed') and 
                                item.get_text() == comp_name):
                                # Connect this arrow's text changes to our composition update
                                if hasattr(item, 'text_changed'):
                                    item.text_changed.connect(self._update_composition_text)
                                    self._signal_connections.append((item, item.text_changed, self._update_composition_text))
    
    def _signal_cleanup(self):
        """Clean up all signal connections."""
        for sender, signal, slot in self._signal_connections:
            try:
                signal.disconnect(slot)
            except (RuntimeError, TypeError):
                pass  # Connection might already be broken
        self._signal_connections.clear()
        
    def _update_identity_text(self, new_name):
        """Update identity references when node names change."""
        import re
        # Replace all instances of 1_oldname with 1_newname
        # This is a bit tricky since we need to find which node changed
        sender = self.sender()
        if sender and hasattr(sender, 'get_text'):
            old_name = sender.get_text()  # This might not work during the change...
            # For now, we'll rebuild the entire text by re-examining the scene
            self._rebuild_identity_text()
    
    def _update_composition_text(self, new_text):
        """Update composition when component arrow text changes."""
        # For composition updates, we'd need to rebuild the entire composition
        # This is complex and might be better handled by the proof step system
        pass
    
    def _rebuild_identity_text(self):
        """Rebuild identity text by examining current node names."""
        import re
        new_text = self._text
        
        # Find all identity patterns and update them with current node names
        identity_matches = re.findall(r'1_([^∘\s]+)', self._text)
        for old_node_name in identity_matches:
            # Find if there's a node that was previously named this
            if self.scene():
                for item in self.scene().items():
                    if (hasattr(item, 'get_text') and 
                        hasattr(item, 'name_changed')):
                        current_name = item.get_text()
                        # Replace the identity reference
                        new_text = re.sub(f'1_{re.escape(old_node_name)}', f'1_{current_name}', new_text)
                        break
        
        if new_text != self._text:
            self.set_text(new_text)
    
    def boundingRect(self):
        """Return the bounding rectangle of the arrow."""
        if not self._start_point or not self._end_point:
            return QRectF(0, 0, 0, 0)
        
        # Calculate bounding box that includes arrow head
        extra = self._arrow_head_size + (self._pen.width() / 2)
        
        if hasattr(self, '_is_self_loop') and self._is_self_loop and hasattr(self, '_loop_center'):
            # For self-loops, use the loop circle bounds
            min_x = self._loop_center.x() - self._loop_radius - extra
            max_x = self._loop_center.x() + self._loop_radius + extra
            min_y = self._loop_center.y() - self._loop_radius - extra
            max_y = self._loop_center.y() + self._loop_radius + extra
        elif hasattr(self, '_is_curved') and self._is_curved and hasattr(self, '_control_point_1'):
            # For curved arrows, include control points in bounds
            all_points = [self._start_point, self._end_point, self._control_point_1, self._control_point_2]
            min_x = min(p.x() for p in all_points) - extra
            max_x = max(p.x() for p in all_points) + extra
            min_y = min(p.y() for p in all_points) - extra
            max_y = max(p.y() for p in all_points) + extra
        else:
            # For normal arrows
            min_x = min(self._start_point.x(), self._end_point.x()) - extra
            max_x = max(self._start_point.x(), self._end_point.x()) + extra
            min_y = min(self._start_point.y(), self._end_point.y()) - extra
            max_y = max(self._start_point.y(), self._end_point.y()) + extra
        
        return QRectF(min_x, min_y, max_x - min_x, max_y - min_y)
    
    def paint(self, painter, option, widget=None):
        """Paint the arrow."""
        if not self._start_point or not self._end_point:
            return
            
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(self._pen)
        
        if hasattr(self, '_is_self_loop') and self._is_self_loop:
            self._paint_self_loop(painter)
        elif hasattr(self, '_is_curved') and self._is_curved:
            self._paint_curved_arrow(painter)
        else:
            self._paint_normal_arrow(painter)
        
        # Draw text label
        self._draw_text_label(painter)
        
        # Draw selection highlight if selected
        if self.isSelected():
            painter.setPen(QPen(QColor(255, 165, 0), 3))  # Orange selection
            if hasattr(self, '_is_self_loop') and self._is_self_loop:
                self._paint_self_loop_outline(painter)
            elif hasattr(self, '_is_curved') and self._is_curved:
                self._paint_curved_arrow_outline(painter)
            else:
                painter.drawLine(self._start_point, self._end_point)
    
    def _paint_normal_arrow(self, painter):
        """Paint a normal arrow between different nodes."""
        # Draw the line
        painter.drawLine(self._start_point, self._end_point)
        
        # Calculate arrow angle
        angle = math.atan2(
            (self._end_point.y() - self._start_point.y()),
            (self._end_point.x() - self._start_point.x())
        )
        
        # Draw arrow tail based on style
        self._draw_arrow_tail(painter, angle)
        
        # Draw arrow head based on style
        self._draw_arrow_head(painter, angle)
    
    def _paint_curved_arrow(self, painter):
        """Paint a curved arrow using bezier curves."""
        from PyQt6.QtGui import QPainterPath
        
        # Create bezier path
        path = QPainterPath()
        path.moveTo(self._start_point)
        path.cubicTo(self._control_point_1, self._control_point_2, self._end_point)
        
        # Draw the curved line
        painter.drawPath(path)
        
        # Calculate arrow head angle at the end point
        # Use the direction from control_point_2 to end_point
        angle = math.atan2(
            (self._end_point.y() - self._control_point_2.y()),
            (self._end_point.x() - self._control_point_2.x())
        )
        
        # Calculate tail angle at start point
        # Use the direction from start_point to control_point_1
        tail_angle = math.atan2(
            (self._control_point_1.y() - self._start_point.y()),
            (self._control_point_1.x() - self._start_point.x())
        )
        
        # Draw arrow tail and head based on style
        self._draw_arrow_tail(painter, tail_angle)
        self._draw_arrow_head(painter, angle)
    
    def _paint_self_loop(self, painter):
        """Paint a self-loop arrow as a circular arc."""
        from PyQt6.QtCore import QRect
        
        # Draw the circular loop
        loop_rect = QRectF(
            self._loop_center.x() - self._loop_radius,
            self._loop_center.y() - self._loop_radius,
            2 * self._loop_radius,
            2 * self._loop_radius
        )
        
        # Draw arc (almost full circle, leaving small gap)
        start_angle = 20 * 16  # 20 degrees in 1/16 degree units
        span_angle = 320 * 16  # 320 degrees span (leaving 40 degree gap)
        
        painter.drawArc(loop_rect, start_angle, span_angle)
        
        # Calculate arrow head position and angle
        end_angle_rad = math.radians(20)  # End at 20 degrees
        arrow_tip_x = self._loop_center.x() + self._loop_radius * math.cos(end_angle_rad)
        arrow_tip_y = self._loop_center.y() + self._loop_radius * math.sin(end_angle_rad)
        arrow_tip = QPointF(arrow_tip_x, arrow_tip_y)
        
        # Calculate arrow head direction (tangent to circle)
        tangent_angle = end_angle_rad + math.pi / 2
        
        # Arrow head points - using smaller angle for pointier arrow head
        arrow_p1 = QPointF(
            arrow_tip.x() - self._arrow_head_size * math.cos(tangent_angle - math.pi / 8),
            arrow_tip.y() - self._arrow_head_size * math.sin(tangent_angle - math.pi / 8)
        )
        
        arrow_p2 = QPointF(
            arrow_tip.x() - self._arrow_head_size * math.cos(tangent_angle + math.pi / 8),
            arrow_tip.y() - self._arrow_head_size * math.sin(tangent_angle + math.pi / 8)
        )
        
        # Draw V-shape arrow head with two lines
        painter.drawLine(arrow_tip, arrow_p1)
        painter.drawLine(arrow_tip, arrow_p2)
    
    def _paint_self_loop_outline(self, painter):
        """Paint selection outline for self-loop."""
        if hasattr(self, '_loop_center') and hasattr(self, '_loop_radius'):
            loop_rect = QRectF(
                self._loop_center.x() - self._loop_radius,
                self._loop_center.y() - self._loop_radius,
                2 * self._loop_radius,
                2 * self._loop_radius
            )
            start_angle = 20 * 16
            span_angle = 320 * 16
            painter.drawArc(loop_rect, start_angle, span_angle)
    
    def _paint_curved_arrow_outline(self, painter):
        """Paint selection outline for curved arrow."""
        from PyQt6.QtGui import QPainterPath
        
        if (hasattr(self, '_control_point_1') and hasattr(self, '_control_point_2') and 
            self._start_point and self._end_point):
            path = QPainterPath()
            path.moveTo(self._start_point)
            path.cubicTo(self._control_point_1, self._control_point_2, self._end_point)
            painter.drawPath(path)
    
    def _draw_text_label(self, painter):
        """Draw the text label in the middle of the arrow, breaking the line."""
        if not self._text or not self._label_visible or self._label_manually_hidden:
            return
        
        # Set up text drawing
        painter.setFont(self._font)
        text_rect = painter.fontMetrics().boundingRect(self._text)
        
        # Calculate text background rectangle (slightly larger than text)
        padding = 4
        bg_width = text_rect.width() + 2 * padding
        bg_height = text_rect.height() + 2 * padding
        
        if hasattr(self, '_is_self_loop') and self._is_self_loop:
            # For self-loops, position text at the far point of the loop
            mid_point = QPointF(
                self._loop_center.x(),
                self._loop_center.y() - self._loop_radius - 10
            )
        elif hasattr(self, '_is_curved') and self._is_curved and hasattr(self, '_control_point_1'):
            # For curved arrows, position text at the curve's peak
            # Use the midpoint between the two control points
            mid_point = QPointF(
                (self._control_point_1.x() + self._control_point_2.x()) / 2,
                (self._control_point_1.y() + self._control_point_2.y()) / 2
            )
        else:
            # For normal arrows, use midpoint
            mid_x = (self._start_point.x() + self._end_point.x()) / 2
            mid_y = (self._start_point.y() + self._end_point.y()) / 2
            mid_point = QPointF(mid_x, mid_y)
        
        # Center the background rectangle on the calculated point
        bg_rect = QRectF(
            mid_point.x() - bg_width / 2,
            mid_point.y() - bg_height / 2,
            bg_width,
            bg_height
        )
        
        # Draw white background to break the line (for normal arrows) or provide contrast (for loops)
        painter.setPen(QPen(QColor(255, 255, 255), 1))
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.drawRect(bg_rect)
        
        # Draw text
        painter.setPen(QPen(QColor(0, 0, 0)))
        painter.drawText(bg_rect, Qt.AlignmentFlag.AlignCenter, self._text)
    
    def update_position(self):
        """Update arrow position based on connected nodes."""
        if self._start_node and self._end_node:
            self.prepareGeometryChange()
            
            # Check if this is a self-loop
            if self._start_node == self._end_node:
                self._update_self_loop_position()
            else:
                self._update_normal_arrow_position()
                # Update curve positioning for parallel arrows
                self._update_curve_positioning()
            
            # Set arrow position to origin for proper scene coordinates
            self.setPos(0, 0)
            self.update()
    
    def _update_normal_arrow_position(self):
        """Update position for normal arrows between different nodes."""
        # Get node positions (the pos() is the center since boundingRect is centered)
        start_center = self._start_node.pos()
        end_center = self._end_node.pos()
        
        # Calculate edge intersection points
        self._start_point = self._get_edge_intersection(
            start_center, end_center, self._start_node
        )
        self._end_point = self._get_edge_intersection(
            end_center, start_center, self._end_node
        )
    
    def _update_self_loop_position(self):
        """Update position for self-loop arrows."""
        # Get node properties
        node_rect = self._start_node.boundingRect()
        node_pos = self._start_node.pos()
        # Since boundingRect is centered around origin, node_pos is the center
        node_center = node_pos
        
        # Find the best side for the loop (side with most empty space)
        best_side = self._find_best_loop_side()
        
        # Calculate loop points based on the best side
        loop_radius = max(node_rect.width(), node_rect.height()) * 0.6
        
        # Calculate edge positions based on centered rectangle
        half_width = node_rect.width() / 2
        half_height = node_rect.height() / 2
        
        if best_side == 'top':
            edge_y = node_pos.y() - half_height
            self._start_point = QPointF(node_center.x() - 10, edge_y)
            self._end_point = QPointF(node_center.x() + 10, edge_y)
            self._loop_center = QPointF(node_center.x(), edge_y - loop_radius)
        elif best_side == 'bottom':
            edge_y = node_pos.y() + half_height
            self._start_point = QPointF(node_center.x() - 10, edge_y)
            self._end_point = QPointF(node_center.x() + 10, edge_y)
            self._loop_center = QPointF(node_center.x(), edge_y + loop_radius)
        elif best_side == 'left':
            edge_x = node_pos.x() - half_width
            self._start_point = QPointF(edge_x, node_center.y() - 10)
            self._end_point = QPointF(edge_x, node_center.y() + 10)
            self._loop_center = QPointF(edge_x - loop_radius, node_center.y())
        else:  # right
            edge_x = node_pos.x() + half_width
            self._start_point = QPointF(edge_x, node_center.y() - 10)
            self._end_point = QPointF(edge_x, node_center.y() + 10)
            self._loop_center = QPointF(edge_x + loop_radius, node_center.y())
        
        self._loop_radius = loop_radius
        self._is_self_loop = True
    
    def _find_best_loop_side(self):
        """Find the side of the node with the most empty space for the loop."""
        node_rect = self._start_node.boundingRect()
        node_pos = self._start_node.pos()
        scene = self._start_node.scene()
        
        if not scene:
            return 'top'  # Default if no scene
        
        # Define areas to check for each side
        check_distance = max(node_rect.width(), node_rect.height()) * 1.5
        
        sides = {
            'top': QRectF(node_pos.x() - check_distance/2, node_pos.y() - check_distance, 
                         node_rect.width() + check_distance, check_distance),
            'bottom': QRectF(node_pos.x() - check_distance/2, node_pos.y() + node_rect.height(), 
                           node_rect.width() + check_distance, check_distance),
            'left': QRectF(node_pos.x() - check_distance, node_pos.y() - check_distance/2, 
                          check_distance, node_rect.height() + check_distance),
            'right': QRectF(node_pos.x() + node_rect.width(), node_pos.y() - check_distance/2, 
                           check_distance, node_rect.height() + check_distance)
        }
        
        # Count objects in each area
        side_scores = {}
        for side, area in sides.items():
            items = scene.items(area)
            # Don't count the node itself
            object_count = sum(1 for item in items if item != self._start_node and hasattr(item, 'get_text'))
            side_scores[side] = object_count
        
        # Return the side with the fewest objects (most empty space)
        return min(side_scores, key=side_scores.get)
    
    @staticmethod
    def update_self_loops_for_node(node):
        """Update all self-loops connected to a node to use the best available side."""
        if not node.scene():
            return
        
        # Find all self-loops for this node - use Arrow class directly
        self_loops = []
        for item in node.scene().items():
            if isinstance(item, Arrow) and item.get_source() == node and item.get_target() == node:
                self_loops.append(item)
        
        # Update position for all self-loops
        for loop in self_loops:
            loop._update_self_loop_position()
            loop.update()
    
    @staticmethod
    def update_parallel_arrows_in_scene(scene):
        """Update curve positioning for all arrows in the scene."""
        if not scene:
            return
        
        # Get all arrows - use Arrow class directly
        arrows = []
        for item in scene.items():
            if isinstance(item, Arrow):
                arrows.append(item)
        
        # Update curve positioning for all arrows
        for arrow in arrows:
            arrow._update_curve_positioning()
            arrow.update()
    
    def _find_parallel_arrows(self):
        """Find arrows that are geometrically parallel and overlapping with this one."""
        if not self.scene() or not self._start_node or not self._end_node:
            return []
        
        parallel_arrows = []
        my_line = self._get_arrow_line()
        
        # Check all other arrows in the scene
        for item in self.scene().items():
            if (isinstance(item, Arrow) and 
                item != self and 
                item._start_node and 
                item._end_node):
                
                # Purely geometric check - ignore node connections completely
                other_line = item._get_arrow_line()
                if self._lines_are_parallel_and_overlapping(my_line, other_line):
                    parallel_arrows.append(item)
        
        return parallel_arrows
    
    def _get_parallel_set(self):
        """Get the complete set of geometrically parallel and overlapping arrows including this one."""
        parallel_arrows = self._find_parallel_arrows()
        return [self] + parallel_arrows
    
    def _are_parallel(self, other_arrow):
        """Check if two arrows are parallel according to the mathematical definition."""
        if not other_arrow._start_node or not other_arrow._end_node:
            return False
        
        # Get both sets and check if they're the same
        my_set = set(self._get_parallel_set())
        other_set = set(other_arrow._get_parallel_set())
        
        return my_set == other_set and len(my_set) > 1
    
    def _get_arrow_line(self):
        """Get the geometric line representation of this arrow."""
        if not self._start_node or not self._end_node:
            return None
            
        start_pos = self._start_node.pos() + self._start_node.boundingRect().center()
        end_pos = self._end_node.pos() + self._end_node.boundingRect().center()
        
        return {
            'start': start_pos,
            'end': end_pos,
            'vector': end_pos - start_pos
        }
    
    def _lines_are_parallel_and_overlapping(self, line1, line2):
        """Check if two lines are parallel and geometrically overlapping."""
        if not line1 or not line2:
            return False
        
        # Special case: if arrows share both endpoints, they definitely overlap
        if (abs(line1['start'].x() - line2['start'].x()) < 1 and
            abs(line1['start'].y() - line2['start'].y()) < 1 and
            abs(line1['end'].x() - line2['end'].x()) < 1 and
            abs(line1['end'].y() - line2['end'].y()) < 1):
            return True
        
        # Special case: if arrows have swapped endpoints (opposite directions, same nodes)
        if (abs(line1['start'].x() - line2['end'].x()) < 1 and
            abs(line1['start'].y() - line2['end'].y()) < 1 and
            abs(line1['end'].x() - line2['start'].x()) < 1 and
            abs(line1['end'].y() - line2['start'].y()) < 1):
            return True
        
        v1 = line1['vector']
        v2 = line2['vector']
        
        # Calculate vector lengths
        v1_length = math.sqrt(v1.x()**2 + v1.y()**2)
        v2_length = math.sqrt(v2.x()**2 + v2.y()**2)
        
        # Skip very short vectors (essentially points)
        if v1_length < 1e-6 or v2_length < 1e-6:
            return False
        
        # Check if vectors are parallel (cross product near zero)
        cross_product = abs(v1.x() * v2.y() - v1.y() * v2.x())
        parallel_threshold = 1e-3 * v1_length * v2_length  # More restrictive threshold
        
        if cross_product > parallel_threshold:
            return False  # Not parallel enough
        
        # Check if lines overlap (not just parallel but intersecting/touching)
        return self._lines_overlap(line1, line2)
    
    def _lines_overlap(self, line1, line2):
        """Check if two parallel line SEGMENTS overlap in their extent."""
        # For line segments, we need to check if they actually overlap in space,
        # not just if their infinite extensions would overlap
        
        v1 = line1['vector']
        v2 = line2['vector']
        v1_len = math.sqrt(v1.x()**2 + v1.y()**2)
        v2_len = math.sqrt(v2.x()**2 + v2.y()**2)
        
        if v1_len == 0 or v2_len == 0:
            return False
        
        # Use the longer segment's direction as reference
        if v1_len >= v2_len:
            ref_dir_x = v1.x() / v1_len
            ref_dir_y = v1.y() / v1_len
        else:
            ref_dir_x = v2.x() / v2_len
            ref_dir_y = v2.y() / v2_len
        
        # Project all four endpoints onto the reference direction
        def project_point(point):
            return point.x() * ref_dir_x + point.y() * ref_dir_y
        
        # Project the endpoints of both segments
        seg1_start_proj = project_point(line1['start'])
        seg1_end_proj = project_point(line1['end'])
        seg2_start_proj = project_point(line2['start'])
        seg2_end_proj = project_point(line2['end'])
        
        # Get the actual segment ranges (not extended lines)
        seg1_min = min(seg1_start_proj, seg1_end_proj)
        seg1_max = max(seg1_start_proj, seg1_end_proj)
        seg2_min = min(seg2_start_proj, seg2_end_proj)
        seg2_max = max(seg2_start_proj, seg2_end_proj)
        
        # Check if the line SEGMENTS overlap (not just their extensions)
        # We also need to check perpendicular distance between the parallel segments
        if not self._segments_overlap_in_projection(seg1_min, seg1_max, seg2_min, seg2_max):
            return False
        
        # Check perpendicular distance between parallel segments
        return self._segments_close_enough_perpendicularly(line1, line2, ref_dir_x, ref_dir_y)
    
    def _segments_overlap_in_projection(self, seg1_min, seg1_max, seg2_min, seg2_max):
        """Check if two segments overlap when projected onto their common direction."""
        # Calculate the actual overlap amount
        overlap_start = max(seg1_min, seg2_min)
        overlap_end = min(seg1_max, seg2_max)
        overlap_length = overlap_end - overlap_start
        
        # For debugging: if segments are very similar (likely same endpoints), consider overlapping
        segment1_length = abs(seg1_max - seg1_min)
        segment2_length = abs(seg2_max - seg2_min)
        
        # If both segments are very similar in position and length, they likely overlap
        if (abs(seg1_min - seg2_min) < 5 and abs(seg1_max - seg2_max) < 5 and
            abs(segment1_length - segment2_length) < 10):
            return True
        
        # Require meaningful overlap, but be less strict than before
        min_overlap_threshold = 10  # Reduced back to 10 units
        
        return overlap_length > min_overlap_threshold
    
    def _segments_close_enough_perpendicularly(self, line1, line2, ref_dir_x, ref_dir_y):
        """Check if parallel segments are close enough perpendicular to their direction."""
        # Calculate perpendicular direction
        perp_dir_x = -ref_dir_y
        perp_dir_y = ref_dir_x
        
        # Project segment midpoints onto perpendicular direction
        line1_mid_x = (line1['start'].x() + line1['end'].x()) / 2
        line1_mid_y = (line1['start'].y() + line1['end'].y()) / 2
        line2_mid_x = (line2['start'].x() + line2['end'].x()) / 2
        line2_mid_y = (line2['start'].y() + line2['end'].y()) / 2
        
        line1_perp_proj = line1_mid_x * perp_dir_x + line1_mid_y * perp_dir_y
        line2_perp_proj = line2_mid_x * perp_dir_x + line2_mid_y * perp_dir_y
        
        # Check perpendicular distance
        perp_distance = abs(line1_perp_proj - line2_perp_proj)
        max_perp_distance = 50  # Maximum distance for segments to be considered "overlapping"
        
        return perp_distance <= max_perp_distance
    
    def _arrows_would_visually_overlap(self, other_arrows):
        """Check if this arrow would visually overlap with other arrows if drawn straight."""
        if not other_arrows:
            return False
        
        my_line = self._get_arrow_line()
        
        # Calculate my arrow's visual thickness (consider line width + some margin)
        arrow_thickness = 6  # Approximate visual thickness including line width and margins
        
        for other_arrow in other_arrows:
            other_line = other_arrow._get_arrow_line()
            
            # Check if lines are parallel and close enough to overlap visually
            if self._lines_are_parallel_and_overlapping(my_line, other_line):
                # Check perpendicular distance between the lines
                my_mid = QPointF(
                    (my_line['start'].x() + my_line['end'].x()) / 2,
                    (my_line['start'].y() + my_line['end'].y()) / 2
                )
                other_mid = QPointF(
                    (other_line['start'].x() + other_line['end'].x()) / 2,
                    (other_line['start'].y() + other_line['end'].y()) / 2
                )
                
                # Calculate perpendicular distance between parallel lines
                direction = my_line['vector']
                direction_length = math.sqrt(direction.x() ** 2 + direction.y() ** 2)
                if direction_length == 0:
                    continue
                    
                # Perpendicular vector
                perp_x = -direction.y() / direction_length
                perp_y = direction.x() / direction_length
                
                # Vector between midpoints
                mid_diff_x = other_mid.x() - my_mid.x()
                mid_diff_y = other_mid.y() - my_mid.y()
                
                # Project onto perpendicular direction
                perp_distance = abs(mid_diff_x * perp_x + mid_diff_y * perp_y)
                
                # If perpendicular distance is less than visual thickness, they overlap
                if perp_distance < arrow_thickness:
                    return True
        
        return False
    
    def _arrows_point_opposite_directions(self, other_arrow):
        """Check if two arrows point in opposite directions."""
        my_vector = self._get_arrow_line()['vector']
        other_vector = other_arrow._get_arrow_line()['vector']
        
        # Calculate dot product to determine if directions are opposite
        dot_product = my_vector.x() * other_vector.x() + my_vector.y() * other_vector.y()
        
        # If dot product is negative, they point in roughly opposite directions
        return dot_product < 0
    
    def _get_direction_factor(self):
        """Get a factor representing the general direction of this arrow."""
        vector = self._get_arrow_line()['vector']
        
        # Use a combination of x and y to create a direction factor
        # This ensures consistent ordering for arrows pointing in different directions
        return vector.x() + vector.y() * 1000  # Weight y more heavily for consistent sorting
    
    def _update_curve_positioning(self):
        """Update bezier curve positioning for parallel arrows."""
        parallel_arrows = self._find_parallel_arrows()
        
        # Only curve if there are actually other parallel/overlapping arrows
        if not parallel_arrows or len(parallel_arrows) == 0:
            # No parallel arrows found, use straight line
            self._is_curved = False
            self._curve_offset = 0
            return
        
        # Double-check: ensure we actually found parallel arrows
        if len(parallel_arrows) == 0:
            self._is_curved = False
            self._curve_offset = 0
            return
        
        # This arrow is part of a parallel group, so curve it
        self._is_curved = True
        
        # Sort all arrows (including self) by some consistent criteria for offset assignment
        all_arrows = [self] + parallel_arrows
        
        # Sort by memory address to ensure consistent ordering
        all_arrows.sort(key=lambda x: id(x))
        
        # Find this arrow's index in the sorted list
        arrow_index = all_arrows.index(self)
        total_arrows = len(all_arrows)
        
        # Calculate curve offset based on position in the group
        base_offset = 30  # Base curve distance
        
        # First check if any arrows share both domain and codomain (same endpoints)
        same_endpoints_arrows = []
        for arrow in parallel_arrows:
            if ((self._start_node == arrow._start_node and self._end_node == arrow._end_node) or
                (self._start_node == arrow._end_node and self._end_node == arrow._start_node)):
                same_endpoints_arrows.append(arrow)
        
        if same_endpoints_arrows:
            # Special case: arrows sharing both endpoints should curve in opposite directions
            same_endpoints_group = [self] + same_endpoints_arrows
            same_endpoints_group.sort(key=lambda x: id(x))  # Consistent ordering
            
            my_index = same_endpoints_group.index(self)
            
            if len(same_endpoints_group) == 2:
                # Two arrows with same endpoints - curve in opposite directions
                self._curve_offset = base_offset if my_index == 0 else -base_offset
            else:
                # More than 2 arrows with same endpoints - spread them out symmetrically
                center_index = (len(same_endpoints_group) - 1) / 2
                offset_multiplier = (my_index - center_index)
                self._curve_offset = offset_multiplier * base_offset
            
            # Use default curve direction calculation
            self._curve_direction = None
            
        else:
            # For arrows that don't share both endpoints, only curve if they would visually overlap
            non_same_endpoint_arrows = []
            for arrow in parallel_arrows:
                # Skip arrows that share both endpoints (already handled above)
                if not ((self._start_node == arrow._start_node and self._end_node == arrow._end_node) or
                        (self._start_node == arrow._end_node and self._end_node == arrow._start_node)):
                    non_same_endpoint_arrows.append(arrow)
            
            # Check if we would actually visually overlap with these arrows
            if not self._arrows_would_visually_overlap(non_same_endpoint_arrows):
                # No visual overlap - don't curve
                self._is_curved = False
                self._curve_offset = 0
                return
            
            # There would be visual overlap, so proceed with curving logic
            # Check if remaining arrows are pointing in roughly the same direction
            same_direction_group = True
            if len(non_same_endpoint_arrows) > 0:
                my_vector = self._get_arrow_line()['vector']
                for other_arrow in non_same_endpoint_arrows:
                    other_vector = other_arrow._get_arrow_line()['vector']
                    dot_product = my_vector.x() * other_vector.x() + my_vector.y() * other_vector.y()
                    if dot_product < 0:  # Opposite directions
                        same_direction_group = False
                        break
            
            if same_direction_group:
                # All arrows point in the same general direction - curve them all to the same side
                # Use a consistent direction for all arrows in the group
                direction_vector = self._get_arrow_line()['vector']
                
                # Calculate perpendicular direction (rotate 90 degrees)
                perp_x = -direction_vector.y()
                perp_y = direction_vector.x()
                
                # Normalize the perpendicular vector
                perp_length = math.sqrt(perp_x * perp_x + perp_y * perp_y)
                if perp_length > 0:
                    perp_x /= perp_length
                    perp_y /= perp_length
                
                # Use a consistent offset direction (always curve "up" relative to arrow direction)
                # Offset each arrow by increasing amounts
                offset_distance = base_offset * (arrow_index + 1)
                self._curve_offset = offset_distance
                
                # Store the perpendicular direction for use in bezier calculation
                self._curve_direction = (perp_x, perp_y)
            else:
                # Mixed directions - use the old logic for opposite direction handling
                if total_arrows == 2:
                    other_arrow = parallel_arrows[0]
                    if self._arrows_point_opposite_directions(other_arrow):
                        # Opposite directions: curve away from each other
                        my_direction_factor = self._get_direction_factor()
                        other_direction_factor = other_arrow._get_direction_factor()
                        
                        # Use direction to determine which way to curve
                        if my_direction_factor > other_direction_factor:
                            self._curve_offset = base_offset
                        else:
                            self._curve_offset = -base_offset
                    else:
                        # Same direction: use normal alternating pattern
                        self._curve_offset = base_offset if arrow_index == 0 else -base_offset
                else:
                    # For more arrows, spread them out considering directions
                    center_index = (total_arrows - 1) / 2
                    offset_multiplier = (arrow_index - center_index)
                    
                    # Adjust for direction if needed
                    direction_factor = self._get_direction_factor()
                    if direction_factor < 0:  # Pointing "backward", flip the offset
                        offset_multiplier = -offset_multiplier
                        
                    self._curve_offset = offset_multiplier * base_offset
                
                # Use default curve direction
                self._curve_direction = None
        
        # Calculate control points for bezier curve
        self._calculate_bezier_control_points()
    
    def _calculate_bezier_control_points(self):
        """Calculate control points for the bezier curve."""
        if not self._is_curved or not self._start_point or not self._end_point:
            return
        
        # Calculate the midpoint and perpendicular direction
        mid_x = (self._start_point.x() + self._end_point.x()) / 2
        mid_y = (self._start_point.y() + self._end_point.y()) / 2
        
        # Use stored curve direction if available, otherwise calculate it
        if hasattr(self, '_curve_direction') and self._curve_direction is not None:
            perp_dx, perp_dy = self._curve_direction
        else:
            # Calculate direction vector
            dx = self._end_point.x() - self._start_point.x()
            dy = self._end_point.y() - self._start_point.y()
            
            # Calculate perpendicular vector (rotate 90 degrees)
            perp_dx = -dy
            perp_dy = dx
            
            # Normalize perpendicular vector
            length = math.sqrt(perp_dx * perp_dx + perp_dy * perp_dy)
            if length > 0:
                perp_dx /= length
                perp_dy /= length
        
        # Apply curve offset
        offset_x = perp_dx * self._curve_offset
        offset_y = perp_dy * self._curve_offset
        
        # Calculate direction vector for control point placement
        dx = self._end_point.x() - self._start_point.x()
        dy = self._end_point.y() - self._start_point.y()
        
        # Control points at 1/3 and 2/3 along the line, offset perpendicular
        t1, t2 = 0.3, 0.7
        
        self._control_point_1 = QPointF(
            self._start_point.x() + t1 * dx + offset_x,
            self._start_point.y() + t1 * dy + offset_y
        )
        
        self._control_point_2 = QPointF(
            self._start_point.x() + t2 * dx + offset_x,
            self._start_point.y() + t2 * dy + offset_y
        )
    
    def _get_edge_intersection(self, center, target_center, node):
        """Calculate the intersection point where the line from center to target_center intersects the node's rounded boundary."""
        # Get node's bounding rectangle and corner radius
        rect = node.boundingRect()
        node_pos = node.pos()
        corner_radius = getattr(node, '_corner_radius', 10)  # Default to 10 if not found
        
        # Convert to scene coordinates
        scene_rect = QRectF(
            node_pos.x() + rect.x(),
            node_pos.y() + rect.y(),
            rect.width(),
            rect.height()
        )
        
        # Calculate direction vector from center to target
        dx = target_center.x() - center.x()
        dy = target_center.y() - center.y()
        
        # If nodes are at the same position, return center
        if abs(dx) < 0.001 and abs(dy) < 0.001:
            return center
        
        # Create rounded rectangle path and convert to line segments
        line_segments = self._get_rounded_rect_segments(scene_rect, corner_radius)
        
        # Find the closest point on the boundary to the line from center to target_center
        closest_point = self._find_closest_point_on_boundary(center, target_center, line_segments)
        
        return closest_point
    
    def _get_rounded_rect_segments(self, rect, corner_radius):
        """Convert a rounded rectangle into a list of line segments."""
        from PyQt6.QtGui import QPainterPath
        
        # Create rounded rectangle path
        path = QPainterPath()
        path.addRoundedRect(rect, corner_radius, corner_radius)
        
        # Convert path to polygons (line segments)
        segments = []
        polygon = path.toFillPolygon()
        
        # Convert polygon points to line segments
        for i in range(len(polygon) - 1):
            segments.append((polygon[i], polygon[i + 1]))
        
        # Close the path if needed
        if len(polygon) > 0:
            segments.append((polygon[-1], polygon[0]))
        
        return segments
    
    def _find_closest_point_on_boundary(self, center, target_center, line_segments):
        """Find the closest point on the boundary segments to the line from center to target_center."""
        # Calculate direction vector from center to target
        dx = target_center.x() - center.x()
        dy = target_center.y() - center.y()
        length = math.sqrt(dx * dx + dy * dy)
        
        if length == 0:
            return center
        
        # Normalize direction vector
        dx_norm = dx / length
        dy_norm = dy / length
        
        closest_point = center
        min_distance = float('inf')
        
        # Check intersection with each line segment
        for segment_start, segment_end in line_segments:
            # Find intersection of ray from center with this line segment
            intersection = self._line_segment_intersection(
                center, QPointF(center.x() + dx_norm * 1000, center.y() + dy_norm * 1000),
                segment_start, segment_end
            )
            
            if intersection:
                # Check if this intersection is in the correct direction
                to_intersection_x = intersection.x() - center.x()
                to_intersection_y = intersection.y() - center.y()
                
                # Check if intersection is in the same direction as target
                dot_product = to_intersection_x * dx_norm + to_intersection_y * dy_norm
                
                if dot_product > 0:  # Same direction
                    distance = math.sqrt(to_intersection_x ** 2 + to_intersection_y ** 2)
                    if distance < min_distance:
                        min_distance = distance
                        closest_point = intersection
        
        return closest_point
    
    def _line_segment_intersection(self, p1, p2, p3, p4):
        """Find intersection point of two line segments (p1-p2 and p3-p4)."""
        x1, y1 = p1.x(), p1.y()
        x2, y2 = p2.x(), p2.y()
        x3, y3 = p3.x(), p3.y()
        x4, y4 = p4.x(), p4.y()
        
        denominator = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        
        if abs(denominator) < 1e-10:
            return None  # Lines are parallel
        
        t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denominator
        u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / denominator
        
        # Check if intersection is within both line segments
        if 0 <= u <= 1:  # Only check if intersection is on the boundary segment
            intersection_x = x1 + t * (x2 - x1)
            intersection_y = y1 + t * (y2 - y1)
            return QPointF(intersection_x, intersection_y)
        
        return None
    
    def set_start_point(self, point):
        """Set the start point of the arrow."""
        self.prepareGeometryChange()
        self._start_point = point
        self.update()
    
    def set_end_point(self, point):
        """Set the end point of the arrow."""
        self.prepareGeometryChange()
        self._end_point = point
        self.update()
    
    def set_nodes(self, start_node, end_node):
        """Set the connected nodes."""
        # Disconnect from old nodes
        if self._start_node:
            self._start_node.node_moved.disconnect(self.update_position)
            if hasattr(self._start_node, 'name_changed'):
                self._start_node.name_changed.disconnect(self._update_label_visibility)
        if self._end_node:
            self._end_node.node_moved.disconnect(self.update_position)
            if hasattr(self._end_node, 'name_changed'):
                self._end_node.name_changed.disconnect(self._update_label_visibility)
        
        # Connect to new nodes
        self._start_node = start_node
        self._end_node = end_node
        
        if self._start_node:
            self._start_node.node_moved.connect(self.update_position)
            if hasattr(self._start_node, 'name_changed'):
                self._start_node.name_changed.connect(self._update_label_visibility)
        if self._end_node:
            self._end_node.node_moved.connect(self.update_position)
            if hasattr(self._end_node, 'name_changed'):
                self._end_node.name_changed.connect(self._update_label_visibility)
            
        self.update_position()
        
        # Update label visibility with new nodes
        self._update_label_visibility()
    
    def type(self):
        """Return the type identifier for this item."""
        return QGraphicsItem.UserType + 2
    
    def _draw_arrow_tail(self, painter, angle):
        """Draw the arrow tail based on style."""
        # Inclusion takes precedence over monomorphism
        if self._is_inclusion:
            self._draw_hook_tail(painter, angle)
        elif self._is_monomorphism:
            self._draw_vee_tail(painter, angle)
    
    def _draw_arrow_head(self, painter, angle):
        """Draw the arrow head based on style."""
        if self._is_epimorphism:
            self._draw_two_head(painter, angle)
        else:
            self._draw_normal_head(painter, angle)
    
    def _draw_hook_tail(self, painter, angle):
        """Draw hook tail for inclusion arrows using rotation and translation approach."""
        hook_size = self._arrow_head_size
        
        # Step 1: Design hook tail for horizontal arrow (parallel to positive X-axis)
        # For a horizontal arrow, the hook tail should be a 180-degree arc
        # positioned above the start point (at origin for now)
        canonical_center_x = 0  # Start point at origin
        canonical_center_y = -hook_size  # Arc center above the start point
        
        # Create arc rectangle for canonical position
        arc_rect = QRectF(
            canonical_center_x - hook_size,
            canonical_center_y - hook_size,
            hook_size * 2,
            hook_size * 2
        )
        
        # For horizontal arrow, start the arc at 90 degrees (top of circle)
        # and draw 180 degrees clockwise
        canonical_start_angle = 90  # degrees
        
        # Step 2: Apply rotation by the arrow's angle
        # Step 3: Apply translation to the arrow's start point
        
        # Save the current painter state
        painter.save()
        
        # Translate to arrow start point
        painter.translate(self._start_point.x(), self._start_point.y())
        
        # Rotate by the arrow's angle
        painter.rotate(math.degrees(angle))
        
        # Draw the arc in the transformed coordinate system
        painter.drawArc(arc_rect, int(canonical_start_angle * 16), int(180 * 16))
        
        # Restore the painter state
        painter.restore()
    
    def _draw_vee_tail(self, painter, angle):
        """Draw vee tail for monomorphism arrows."""
        vee_size = self._arrow_head_size
        
        # Vee points
        vee_p1 = QPointF(
            self._start_point.x() + vee_size * math.cos(angle - math.pi / 6),
            self._start_point.y() + vee_size * math.sin(angle - math.pi / 6)
        )
        vee_p2 = QPointF(
            self._start_point.x() + vee_size * math.cos(angle + math.pi / 6),
            self._start_point.y() + vee_size * math.sin(angle + math.pi / 6)
        )
        
        # Draw vee tail
        painter.drawLine(self._start_point, vee_p1)
        painter.drawLine(self._start_point, vee_p2)
    
    def _draw_two_head(self, painter, angle):
        """Draw double arrow head for epimorphism arrows."""
        head_size = self._arrow_head_size
        offset_distance = head_size * 0.6
        
        # First arrow head (at tip)
        arrow1_p1 = QPointF(
            self._end_point.x() - head_size * math.cos(angle - math.pi / 8),
            self._end_point.y() - head_size * math.sin(angle - math.pi / 8)
        )
        arrow1_p2 = QPointF(
            self._end_point.x() - head_size * math.cos(angle + math.pi / 8),
            self._end_point.y() - head_size * math.sin(angle + math.pi / 8)
        )
        
        # Second arrow head (offset back)
        head2_center = QPointF(
            self._end_point.x() - offset_distance * math.cos(angle),
            self._end_point.y() - offset_distance * math.sin(angle)
        )
        arrow2_p1 = QPointF(
            head2_center.x() - head_size * math.cos(angle - math.pi / 8),
            head2_center.y() - head_size * math.sin(angle - math.pi / 8)
        )
        arrow2_p2 = QPointF(
            head2_center.x() - head_size * math.cos(angle + math.pi / 8),
            head2_center.y() - head_size * math.sin(angle + math.pi / 8)
        )
        
        # Draw both arrow heads
        painter.drawLine(self._end_point, arrow1_p1)
        painter.drawLine(self._end_point, arrow1_p2)
        painter.drawLine(head2_center, arrow2_p1)
        painter.drawLine(head2_center, arrow2_p2)
    
    def _draw_normal_head(self, painter, angle):
        """Draw normal single arrow head."""
        arrow_p1 = QPointF(
            self._end_point.x() - self._arrow_head_size * math.cos(angle - math.pi / 8),
            self._end_point.y() - self._arrow_head_size * math.sin(angle - math.pi / 8)
        )
        arrow_p2 = QPointF(
            self._end_point.x() - self._arrow_head_size * math.cos(angle + math.pi / 8),
            self._end_point.y() - self._arrow_head_size * math.sin(angle + math.pi / 8)
        )
        
        # Draw V-shape arrow head with two lines
        painter.drawLine(self._end_point, arrow_p1)
        painter.drawLine(self._end_point, arrow_p2)
    
    def get_text(self):
        """Get the text displayed on the arrow."""
        if self._is_isomorphism:
            return f"~ {self._text}"
        return self._text
    
    def set_text(self, text):
        """Set the text displayed on the arrow."""
        old_text = self._text
        self._text = text
        self.update()
        
        # Emit signal if text actually changed
        if old_text != text:
            self.text_changed.emit(text)
    
    def set_base_name(self, name):
        """Set the base name of the arrow (without formatting prefixes)."""
        old_text = self._text
        self.set_text(name)
        
        # Update label visibility when name changes
        if old_text != name:
            self._update_label_visibility()
    
    def get_base_name(self):
        """Get the base name of the arrow (without formatting prefixes)."""
        return self._text
    
    def _should_hide_label(self):
        """Check if the arrow label should be hidden based on naming conditions."""
        # Hide label if arrow's base name is "0" and either source or target base name is also "0"
        if self._text != "0":
            return False
            
        if self._start_node and hasattr(self._start_node, 'get_text'):
            if self._start_node.get_text() == "0":
                return True
                
        if self._end_node and hasattr(self._end_node, 'get_text'):
            if self._end_node.get_text() == "0":
                return True
                
        return False
    
    def _update_label_visibility(self):
        """Update label visibility based on current conditions."""
        should_hide = self._should_hide_label()
        if self._label_visible == should_hide:  # Need to toggle
            self._label_visible = not should_hide
            self.update()  # Trigger repaint
    
    def set_there_exists(self, exists):
        """Set the 'There Exists' state (dashed line when True)."""
        self._there_exists = exists
        self._update_pen_style()
        self.update()
    
    def get_there_exists(self):
        """Get the current 'There Exists' state."""
        return self._there_exists
    
    def toggle_there_exists(self):
        """Toggle the 'There Exists' state."""
        self.set_there_exists(not self._there_exists)
    
    def toggle_inclusion(self):
        """Toggle the inclusion (hook tail) style."""
        # Kernel arrows cannot have their inclusion status changed
        if self.is_kernel_arrow():
            return
        self._is_inclusion = not self._is_inclusion
        if self._is_inclusion:
            self._is_general = False
        self._update_style()
    
    def toggle_monomorphism(self):
        """Toggle the monomorphism (vee tail) style."""
        # Kernel arrows cannot be monomorphisms
        if self.is_kernel_arrow():
            return
        self._is_monomorphism = not self._is_monomorphism
        if self._is_monomorphism:
            self._is_general = False
        self._update_style()
    
    def toggle_epimorphism(self):
        """Toggle the epimorphism (two head) style."""
        self._is_epimorphism = not self._is_epimorphism
        if self._is_epimorphism:
            self._is_general = False
        self._update_style()
    
    def toggle_isomorphism(self):
        """Toggle the isomorphism (similarity arrow) style."""
        self._is_isomorphism = not self._is_isomorphism
        if self._is_isomorphism:
            self._is_general = False
        self._update_style()
    
    def toggle_general(self):
        """Toggle general arrow style (mutually exclusive with others)."""
        # Kernel arrows cannot be general arrows
        if self.is_kernel_arrow():
            return
        if not self._is_general:  # Only if not already general
            self._is_general = True
            self._is_inclusion = False
            self._is_monomorphism = False
            self._is_epimorphism = False
            self._is_isomorphism = False
            self._update_style()
    
    def toggle_label_visibility(self):
        """Toggle manual label visibility."""
        self._label_manually_hidden = not self._label_manually_hidden
        self.update()  # Trigger repaint
    
    def is_kernel_arrow(self):
        """Check if this arrow is a kernel arrow based on its name."""
        return self._is_kernel_arrow or self._text.startswith("k_")
    
    def set_as_kernel_arrow(self):
        """Mark this arrow as a kernel arrow and automatically set it as inclusion."""
        self._is_kernel_arrow = True
        # Kernel arrows are automatically inclusions
        self._is_inclusion = True
        self._is_monomorphism = False
        self._is_epimorphism = False
        self._is_isomorphism = False
        self._is_general = False
        self._update_style()
    
    def _update_style(self):
        """Update arrow appearance based on style settings."""
        self.update()  # Trigger repaint
    
    def _update_pen_style(self):
        """Update the pen style based on the 'There Exists' state."""
        from PyQt6.QtCore import Qt
        
        if self._there_exists:
            # Create dashed pen
            dashed_pen = QPen(self._solid_pen)
            dashed_pen.setStyle(Qt.PenStyle.DashLine)
            self._pen = dashed_pen
        else:
            # Use solid pen
            self._pen = QPen(self._solid_pen)
        
        # Update original pen for highlight restoration
        self._original_pen = self._pen
    
    def get_source(self):
        """Get the source node of the arrow."""
        return self._start_node
    
    def get_target(self):
        """Get the target node of the arrow."""
        return self._end_node
    
    def contextMenuEvent(self, event):
        """Handle right-click context menu."""
        menu = QMenu()
        
        # Add "Edit Name" action
        edit_name_action = QAction("Edit Name", menu)
        edit_name_action.triggered.connect(self.edit_name)
        menu.addAction(edit_name_action)
        
        # Add "Hide Label" toggle action
        hide_label_action = QAction("Hide Label", menu)
        hide_label_action.setCheckable(True)
        hide_label_action.setChecked(self._label_manually_hidden)
        hide_label_action.triggered.connect(self.toggle_label_visibility)
        menu.addAction(hide_label_action)
        
        # Add "Flip Arrow" action
        flip_action = QAction("Flip Arrow", menu)
        flip_action.triggered.connect(self.flip_arrow)
        menu.addAction(flip_action)
        
        # Add separator
        menu.addSeparator()
        
        # Add "There Exists" toggle action
        there_exists_action = QAction("There Exists", menu)
        there_exists_action.setCheckable(True)
        there_exists_action.setChecked(self._there_exists)
        there_exists_action.triggered.connect(self.toggle_there_exists)
        menu.addAction(there_exists_action)
        
        # Add separator for arrow styles
        menu.addSeparator()
        
        # Different menu options for kernel arrows vs regular arrows
        if self.is_kernel_arrow():
            # For kernel arrows, only show Inclusion (checked and disabled), Isomorphism, and Epimorphism
            inclusion_action = QAction("Inclusion", menu)
            inclusion_action.setCheckable(True)
            inclusion_action.setChecked(True)  # Always checked for kernel arrows
            inclusion_action.setEnabled(False)  # Disabled - cannot be changed
            menu.addAction(inclusion_action)
            
            isomorphism_action = QAction("Isomorphism", menu)
            isomorphism_action.setCheckable(True)
            isomorphism_action.setChecked(self._is_isomorphism)
            isomorphism_action.triggered.connect(self.toggle_isomorphism)
            menu.addAction(isomorphism_action)
            
            epimorphism_action = QAction("Epimorphism", menu)
            epimorphism_action.setCheckable(True)
            epimorphism_action.setChecked(self._is_epimorphism)
            epimorphism_action.triggered.connect(self.toggle_epimorphism)
            menu.addAction(epimorphism_action)
            
        else:
            # For regular arrows, show all arrow style toggles
            inclusion_action = QAction("Inclusion", menu)
            inclusion_action.setCheckable(True)
            inclusion_action.setChecked(self._is_inclusion)
            inclusion_action.triggered.connect(self.toggle_inclusion)
            menu.addAction(inclusion_action)
            
            monomorphism_action = QAction("Monomorphism", menu)
            monomorphism_action.setCheckable(True)
            monomorphism_action.setChecked(self._is_monomorphism)
            monomorphism_action.triggered.connect(self.toggle_monomorphism)
            menu.addAction(monomorphism_action)
            
            epimorphism_action = QAction("Epimorphism", menu)
            epimorphism_action.setCheckable(True)
            epimorphism_action.setChecked(self._is_epimorphism)
            epimorphism_action.triggered.connect(self.toggle_epimorphism)
            menu.addAction(epimorphism_action)
            
            isomorphism_action = QAction("Isomorphism", menu)
            isomorphism_action.setCheckable(True)
            isomorphism_action.setChecked(self._is_isomorphism)
            isomorphism_action.triggered.connect(self.toggle_isomorphism)
            menu.addAction(isomorphism_action)
            
            general_action = QAction("General Arrow", menu)
            general_action.setCheckable(True)
            general_action.setChecked(self._is_general)
            general_action.triggered.connect(self.toggle_general)
            menu.addAction(general_action)
        
        # Add separator
        menu.addSeparator()
        
        # Add "Delete" action
        delete_action = QAction("Delete", menu)
        delete_action.triggered.connect(self.delete_arrow)
        menu.addAction(delete_action)
        
        # Show the menu at the cursor position
        menu.exec(event.screenPos())
    
    def edit_name(self):
        """Open the rename dialog to edit the arrow's name."""
        from dialog.arrow_rename_dialog import ArrowRenameDialog
        from core.undo_commands import RenameArrow
        from PyQt6.QtWidgets import QApplication
        
        dialog = ArrowRenameDialog(self._text, self.scene().views()[0])
        if dialog.exec() == dialog.DialogCode.Accepted:
            new_name = dialog.get_name()
            if new_name and new_name != self._text:  # Compare with base text
                # Create and push undo command
                command = RenameArrow(self, self._text, new_name)
                app = QApplication.instance()
                app.undo_stack.push(command)
    
    def delete_arrow(self):
        """Delete this arrow."""
        from core.undo_commands import DeleteItems
        from PyQt6.QtWidgets import QApplication
        
        command = DeleteItems(self.scene(), [self])
        app = QApplication.instance()
        app.undo_stack.push(command)
    
    def flip_arrow(self):
        """Flip the direction of this arrow by swapping source and target."""
        from core.undo_commands import FlipArrowCommand
        from PyQt6.QtWidgets import QApplication
        
        command = FlipArrowCommand(self)
        app = QApplication.instance()
        app.undo_stack.push(command)
    
    def set_highlight_color(self, color):
        """Set highlight color for cycle detection."""
        self._highlight_color = color
        if color:
            # Create highlighted pen and brush
            self._pen = QPen(color, 4)  # Thicker red line
            self._brush = QBrush(color)  # Red arrowhead
        else:
            # Restore original colors
            self._pen = self._original_pen
            self._brush = self._original_brush
        self.update()
    
    def clear_highlight_color(self):
        """Clear highlight color."""
        self.set_highlight_color(None)
