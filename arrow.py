"""
Arrow node for connecting objects in DAG diagrams.
"""
from PyQt6.QtWidgets import QGraphicsItem, QMenu
from PyQt6.QtCore import QRectF, QPointF, Qt
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QPolygonF, QFont, QAction
import math
from node import Node


class Arrow(Node):
    """Arrow node for connecting objects in the DAG."""
    
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
        self._font = QFont("Arial", 9)
        
        # Arrow-specific styling
        self._pen = QPen(QColor(100, 100, 100), 2)
        self._brush = QBrush(QColor(100, 100, 100))
        self._arrow_head_size = 15
        
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
        if self._end_node:
            self._end_node.node_moved.connect(self.update_position)
            
        self.update_position()
    
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
        
        # Calculate arrow head
        angle = math.atan2(
            (self._end_point.y() - self._start_point.y()),
            (self._end_point.x() - self._start_point.x())
        )
        
        # Arrow head points - using smaller angle for pointier arrow head
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
        
        # Arrow head points - using smaller angle for pointier arrow head
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
        if not self._text:
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
        
        from arrow import Arrow
        # Find all self-loops for this node
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
        
        from arrow import Arrow
        arrows = []
        for item in scene.items():
            if isinstance(item, Arrow):
                arrows.append(item)
        
        # Update curve positioning for all arrows
        for arrow in arrows:
            arrow._update_curve_positioning()
            arrow.update()
    
    def _find_parallel_arrows(self):
        """Find arrows that are parallel to this one based on mathematical definition."""
        if not self.scene() or not self._start_node or not self._end_node:
            return []
        
        # Find the set S of all arrows between the same two distinct objects
        parallel_set = self._get_parallel_set()
        
        # Remove self from the set to get other parallel arrows
        parallel_arrows = [arrow for arrow in parallel_set if arrow != self]
        return parallel_arrows
    
    def _get_parallel_set(self):
        """Get the complete set S of parallel arrows including this one."""
        if not self.scene() or not self._start_node or not self._end_node:
            return [self]
        
        # Get the two distinct objects X and Y for this arrow
        X = self._start_node
        Y = self._end_node
        
        # If X and Y are the same (self-loop), no parallel arrows possible
        if X == Y:
            return [self]
        
        # Find all arrows in the scene that connect between X and Y
        parallel_set = []
        for item in self.scene().items():
            if isinstance(item, Arrow):
                if (item._start_node and item._end_node and 
                    item._start_node != item._end_node):  # Not a self-loop
                    
                    # Check if both source and target are in {X, Y}
                    source_in_set = item._start_node in {X, Y}
                    target_in_set = item._end_node in {X, Y}
                    
                    if source_in_set and target_in_set:
                        parallel_set.append(item)
        
        return parallel_set
    
    def _are_parallel(self, other_arrow):
        """Check if two arrows are parallel according to the mathematical definition."""
        if not other_arrow._start_node or not other_arrow._end_node:
            return False
        
        # Get both sets and check if they're the same
        my_set = set(self._get_parallel_set())
        other_set = set(other_arrow._get_parallel_set())
        
        return my_set == other_set and len(my_set) > 1
    
    def _update_curve_positioning(self):
        """Update bezier curve positioning for parallel arrows."""
        parallel_arrows = self._find_parallel_arrows()
        
        if not parallel_arrows:
            # No parallel arrows, use straight line
            self._is_curved = False
            self._curve_offset = 0
            return
        
        # This arrow is part of a parallel group
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
        if total_arrows == 2:
            # For 2 arrows, curve in opposite directions
            self._curve_offset = base_offset if arrow_index == 0 else -base_offset
        else:
            # For more arrows, spread them out
            center_index = (total_arrows - 1) / 2
            offset_multiplier = (arrow_index - center_index)
            self._curve_offset = offset_multiplier * base_offset
        
        # Calculate control points for bezier curve
        self._calculate_bezier_control_points()
    
    def _calculate_bezier_control_points(self):
        """Calculate control points for the bezier curve."""
        if not self._is_curved or not self._start_point or not self._end_point:
            return
        
        # Calculate the midpoint and perpendicular direction
        mid_x = (self._start_point.x() + self._end_point.x()) / 2
        mid_y = (self._start_point.y() + self._end_point.y()) / 2
        
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
        if self._end_node:
            self._end_node.node_moved.disconnect(self.update_position)
        
        # Connect to new nodes
        self._start_node = start_node
        self._end_node = end_node
        
        if self._start_node:
            self._start_node.node_moved.connect(self.update_position)
        if self._end_node:
            self._end_node.node_moved.connect(self.update_position)
            
        self.update_position()
    
    def type(self):
        """Return the type identifier for this item."""
        return QGraphicsItem.UserType + 2
    
    def get_text(self):
        """Get the text displayed on the arrow."""
        return self._text
    
    def set_text(self, text):
        """Set the text displayed on the arrow."""
        self._text = text
        self.update()
    
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
        
        # Add "Flip Arrow" action
        flip_action = QAction("Flip Arrow", menu)
        flip_action.triggered.connect(self.flip_arrow)
        menu.addAction(flip_action)
        
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
        from arrow_rename_dialog import ArrowRenameDialog
        from undo_commands import RenameArrow
        from PyQt6.QtWidgets import QApplication
        
        dialog = ArrowRenameDialog(self._text, self.scene().views()[0])
        if dialog.exec() == dialog.DialogCode.Accepted:
            new_name = dialog.get_name()
            if new_name and new_name != self._text:  # Only update if name changed
                # Create and push undo command
                command = RenameArrow(self, self._text, new_name)
                app = QApplication.instance()
                app.undo_stack.push(command)
    
    def delete_arrow(self):
        """Delete this arrow."""
        from undo_commands import DeleteItems
        from PyQt6.QtWidgets import QApplication
        
        command = DeleteItems(self.scene(), [self])
        app = QApplication.instance()
        app.undo_stack.push(command)
    
    def flip_arrow(self):
        """Flip the direction of this arrow by swapping source and target."""
        from undo_commands import FlipArrowCommand
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
