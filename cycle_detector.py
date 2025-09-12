"""
Cycle detection for directed graphs in the DAG editor.
Implements DFS-based cycle detection with path tracking.
"""

from typing import List, Set, Dict, Tuple, Optional
from enum import Enum

class NodeState(Enum):
    WHITE = 0  # Unvisited
    GRAY = 1   # Being processed (in current DFS path)
    BLACK = 2  # Finished processing

class CycleDetector:
    """Detects cycles in a directed graph and returns cycle paths."""
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        """Reset the detector state."""
        self.node_states: Dict = {}
        self.parent: Dict = {}
        self.cycles: List[List] = []
    
    def find_cycles(self, nodes, arrows) -> List[List]:
        """
        Find all cycles in the graph.
        
        Args:
            nodes: List of node objects
            arrows: List of arrow objects with _start_node and _end_node
            
        Returns:
            List of cycles, where each cycle is a list of nodes in the cycle
        """
        self.reset()
        
        # Initialize all nodes as unvisited
        for node in nodes:
            self.node_states[node] = NodeState.WHITE
            self.parent[node] = None
        
        # Build adjacency list
        adjacency = self._build_adjacency_list(nodes, arrows)
        
        # Run DFS from each unvisited node
        for node in nodes:
            if self.node_states[node] == NodeState.WHITE:
                self._dfs_visit(node, adjacency, [])
        
        return self.cycles
    
    def _build_adjacency_list(self, nodes, arrows) -> Dict:
        """Build adjacency list from arrows."""
        adjacency = {}
        
        # Initialize empty lists for all nodes
        for node in nodes:
            adjacency[node] = []
        
        # Add edges from arrows
        for arrow in arrows:
            if (hasattr(arrow, '_start_node') and hasattr(arrow, '_end_node') and
                arrow._start_node and arrow._end_node and
                arrow._start_node in nodes and arrow._end_node in nodes):
                adjacency[arrow._start_node].append(arrow._end_node)
        
        return adjacency
    
    def _dfs_visit(self, node, adjacency: Dict, current_path: List):
        """
        DFS visit with cycle detection.
        
        Args:
            node: Current node being visited
            adjacency: Adjacency list representation
            current_path: Current DFS path (for cycle reconstruction)
        """
        self.node_states[node] = NodeState.GRAY
        current_path.append(node)
        
        # Visit all neighbors
        for neighbor in adjacency.get(node, []):
            if self.node_states[neighbor] == NodeState.GRAY:
                # Back edge found - we have a cycle
                cycle_start_index = current_path.index(neighbor)
                cycle = current_path[cycle_start_index:] + [neighbor]
                self.cycles.append(cycle)
            elif self.node_states[neighbor] == NodeState.WHITE:
                self._dfs_visit(neighbor, adjacency, current_path)
        
        # Finished processing this node
        self.node_states[node] = NodeState.BLACK
        current_path.pop()
    
    def get_cycle_arrows(self, cycle_nodes, arrows) -> List:
        """
        Get the arrows that form a cycle.
        
        Args:
            cycle_nodes: List of nodes in the cycle (includes duplicate start/end node)
            arrows: List of all arrows
            
        Returns:
            List of arrows that form the cycle
        """
        if len(cycle_nodes) < 2:
            return []
        
        cycle_arrows = []
        
        # For each consecutive pair in the cycle
        for i in range(len(cycle_nodes) - 1):
            start_node = cycle_nodes[i]
            end_node = cycle_nodes[i + 1]
            
            # Find the arrow connecting these nodes
            for arrow in arrows:
                if (hasattr(arrow, '_start_node') and hasattr(arrow, '_end_node') and
                    arrow._start_node == start_node and arrow._end_node == end_node):
                    cycle_arrows.append(arrow)
                    break
        
        return cycle_arrows
