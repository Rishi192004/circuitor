from typing import List
from src.models.circuit import Circuit
from src.models.hint import SimulationHint
from src.hints.base import Hint

class NoLoadSourceHint(Hint):
    """
    Detects voltage sources where one terminal is not connected to a load.
    """

    @property
    def hint_id(self) -> str:
        return "NO_LOAD_SOURCE"

    def check(self, circuit: Circuit) -> List[SimulationHint]:
        hints = []
        
        for comp in circuit.components.values():
            if comp.type == "dc_voltage_source":
                # A source is 'loaded' if it can drive current through at least one 
                # non-source, non-ground component.
                # We'll check if any 'load' component is reachable from either pin.
                
                reachable_loads = False
                for pin_name in ["positive", "negative"]:
                    # BFS to find any load component
                    visited = set()
                    queue = [(comp.id, pin_name)]
                    
                    while queue:
                        curr_comp_id, curr_pin = queue.pop(0)
                        if (curr_comp_id, curr_pin) in visited:
                            continue
                        visited.add((curr_comp_id, curr_pin))
                        
                        # Find net for this pin
                        target_net = None
                        for net in circuit.nets.values():
                            if any(ep.component_id == curr_comp_id and ep.pin_name == curr_pin for ep in net.endpoints):
                                target_net = net
                                break
                        
                        if not target_net: continue
                        
                        # Check all components in this net
                        for ep in target_net.endpoints:
                            if ep.component_id == comp.id: continue # Skip self
                            
                            t_comp = circuit.components.get(ep.component_id)
                            if not t_comp: continue
                            
                            if t_comp.type not in ["dc_voltage_source", "ground"]:
                                reachable_loads = True
                                break
                            
                            # If it's a source, we can continue searching through its pins
                            if t_comp.type == "dc_voltage_source":
                                for p in ["positive", "negative"]:
                                    if (t_comp.id, p) not in visited:
                                        queue.append((t_comp.id, p))
                        
                        if reachable_loads: break
                    if reachable_loads: break
                
                if not reachable_loads:
                    hints.append(SimulationHint(
                        hint_id=self.hint_id,
                        message=f"Voltage source '{comp.id}' has no load. Simulation will show open-circuit voltage only.",
                        target_component_ids=[comp.id]
                    ))
        
        return hints
