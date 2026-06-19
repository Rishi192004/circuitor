from typing import List
from src.models.circuit import Circuit
from src.models.hint import SimulationHint
from src.hints.base import Hint

class HighValueResistorHint(Hint):
    @property
    def hint_id(self) -> str:
        return "HIGH_VALUE_RESISTOR"

    def check(self, circuit: Circuit) -> List[SimulationHint]:
        """
        Detects resistors with very high resistance (> 1M Ohm) which can cause noise sensitivity.
        """
        hints = []
        THRESHOLD = 1_000_000
        
        for comp_id, comp in circuit.components.items():
            if comp.type == "resistor":
                r_str = comp.properties.get("resistance", "0")
                try:
                    val = str(r_str).lower()
                    if 'k' in val: v = float(val.replace('k', '')) * 1000
                    elif 'm' in val: v = float(val.replace('m', '')) * 1000000
                    else: v = float(val)
                    
                    if v >= THRESHOLD:
                        hints.append(SimulationHint(
                            hint_id=self.hint_id,
                            message=f"Resistor '{comp_id}' has a very high value ({r_str}). This can make the node highly sensitive to noise.",
                            target_component_ids=[comp_id]
                        ))
                except:
                    continue
        return hints
