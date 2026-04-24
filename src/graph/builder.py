import logging
from typing import Dict, List, Set, Tuple
from src.models.circuit import Circuit
from src.models.net import Net, PinConnection

logger = logging.getLogger(__name__)

class GraphBuilder:
    def __init__(self, circuit: Circuit):
        self.circuit = circuit
        # Adjacency list representation: component_id.pin -> list of component_id.pin
        self.adjacency_list: Dict[str, List[str]] = {}
        
    def build(self) -> Dict[str, List[str]]:
        """
        Builds a graph representing the circuit connections.
        Each node is a pin (e.g., 'Q1.collector') and edges represent nets connecting them.
        """
        logger.info("Building circuit graph...")
        self.adjacency_list.clear()
        
        for net_id, net in self.circuit.nets.items():
            connections = net.endpoints
            # Connect all pins in the same net to each other (clique)
            for i, conn1 in enumerate(connections):
                node1 = str(conn1)
                if node1 not in self.adjacency_list:
                    self.adjacency_list[node1] = []
                    
                for j, conn2 in enumerate(connections):
                    if i != j:
                        node2 = str(conn2)
                        self.adjacency_list[node1].append(node2)
                        
        logger.info(f"Graph built with {len(self.adjacency_list)} nodes.")
        return self.adjacency_list
        
    def print_connections(self):
        """Prints the graph connections in a readable format."""
        logger.info("Circuit Connections:")
        visited_edges: Set[Tuple[str, str]] = set()
        
        for node, neighbors in self.adjacency_list.items():
            for neighbor in neighbors:
                # Create a canonical edge representation to avoid printing A <-> B and B <-> A
                edge = tuple(sorted([node, neighbor]))
                if edge not in visited_edges:
                    visited_edges.add(edge)
                    print(f"{node} <-> {neighbor}")
