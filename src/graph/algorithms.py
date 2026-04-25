import logging
from typing import List, Dict, Set
from src.models.circuit import Circuit

logger = logging.getLogger(__name__)

def find_source_cycles(circuit: Circuit) -> List[List[str]]:
    """
    Finds cycles in the circuit that consist entirely of voltage/current sources.
    Uses a bipartite graph (Components <-> Nets) to detect parallel loops (KVL violations).
    Returns a list of cycles, where each cycle is a list of component IDs.
    """
    graph: Dict[str, List[str]] = {}
    
    # 1. Identify all source components
    source_ids = []
    for comp_id, comp in circuit.components.items():
        template = circuit.component_templates.get(comp.type)
        if template and template.category == "source":
            source_ids.append(comp_id)
            graph[comp_id] = []
            
    if not source_ids:
        return []
        
    # 2. Build Bipartite Graph (Sources connected to Nets)
    for net_id, net in circuit.nets.items():
        connected_sources = set()
        for ep in net.endpoints:
            if ep.component_id in source_ids:
                connected_sources.add(ep.component_id)
                
        if connected_sources:
            graph[net_id] = []
            for src_id in connected_sources:
                graph[src_id].append(net_id)
                graph[net_id].append(src_id)
                
    # 3. Find cycles using DFS
    visited = set()
    cycles = []
    
    def dfs(current: str, parent: str, path: List[str]):
        visited.add(current)
        path.append(current)
        
        for neighbor in graph.get(current, []):
            if neighbor == parent:
                continue
                
            if neighbor in visited:
                # Found a back-edge -> Cycle!
                if neighbor in path:
                    idx = path.index(neighbor)
                    cycle_nodes = path[idx:]
                    
                    # Filter out Nets, keep only Component IDs
                    source_cycle = [node for node in cycle_nodes if node in source_ids]
                    
                    # We only care about loops involving > 1 source 
                    # (single source shorts are caught by ShortCircuitSourceRule)
                    if len(source_cycle) > 1:
                        # Deduplicate by sorting
                        sorted_cycle = sorted(source_cycle)
                        if sorted_cycle not in [sorted(c) for c in cycles]:
                            cycles.append(source_cycle)
            else:
                dfs(neighbor, current, path)
                
        path.pop()
        
    # Run DFS from every source
    for src in source_ids:
        if src not in visited:
            dfs(src, None, [])
            
    if cycles:
        logger.debug(f"Detected {len(cycles)} source loops: {cycles}")
        
    return cycles
