from typing import List
from src.models.circuit import Circuit
from src.models.hint import SimulationHint
from src.hints.base import Hint

class FloatingOpAmpInputHint(Hint):
    """
    Detects if an Op-Amp's non-inverting (+) or inverting (-) input is left floating.
    While sometimes used in specialized circuits, it's usually an error or leads to 
    unpredictable simulation results.
    """

    @property
    def hint_id(self) -> str:
        return "FLOATING_OPAMP_INPUT"

    def check(self, circuit: Circuit) -> List[SimulationHint]:
        hints = []
        
        INPUT_PINS = {"non_inverting", "inverting", "+", "-", "in+", "in-"}
        
        # Build set of all pins connected to a net
        connected_pins = set()
        for net in circuit.nets.values():
            for ep in net.endpoints:
                connected_pins.add((ep.component_id, ep.pin_name))

        for comp_id, comp in circuit.components.items():
            if comp.type == "op_amp":
                template = circuit.component_templates.get(comp.type)
                if not template: continue
                
                for pin in template.pins_template:
                    if pin.name.lower() in INPUT_PINS:
                        if (comp_id, pin.name) not in connected_pins:
                            hints.append(SimulationHint(
                                hint_id=self.hint_id,
                                message=f"Op-Amp '{comp_id}' has a floating input pin '{pin.name}'. Simulation may show erratic behavior or rail-slamming.",
                                target_component_ids=[comp_id]
                            ))
                            
        return hints
