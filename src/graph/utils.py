from typing import Dict, List

def get_connected_components(adjacency_list: Dict[str, List[str]]) -> List[List[str]]:
    """Finds all isolated subnetworks in the circuit."""
    visited = set()
    components = []
    
    for node in adjacency_list:
        if node not in visited:
            component = []
            queue = [node]
            visited.add(node)
            
            while queue:
                curr = queue.pop(0)
                component.append(curr)
                for neighbor in adjacency_list.get(curr, []):
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)
            components.append(component)
            
    return components
