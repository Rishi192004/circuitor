from typing import List
from src.models.circuit import Circuit
from src.models.validation import ValidationIssue
from src.models.suggestion import PatternSuggestion
from src.patterns.base import Pattern

class LowPassFilterPattern(Pattern):
    @property
    def pattern_id(self) -> str:
        return "RC_LOW_PASS_FILTER"

    @property
    def priority(self) -> int:
        return 60

    def match(self, circuit: Circuit, validation_issues: List[ValidationIssue]) -> List[PatternSuggestion]:
        """
        Detects a resistor in series followed by a capacitor to ground (RC Low Pass Filter).
        """
        suggestions = []
        
        ground_nets = set()
        for comp_id, comp in circuit.components.items():
            if "ground" in comp.type or "ground" in comp_id.lower():
                for net_id, net in circuit.nets.items():
                    if any(ep.component_id == comp_id for ep in net.endpoints):
                        ground_nets.add(net_id)

        for net_id, net in circuit.nets.items():
            resistor_id = None
            capacitor_id = None
            
            for ep in net.endpoints:
                comp = circuit.components.get(ep.component_id)
                if not comp: continue
                if comp.type == "resistor":
                    resistor_id = comp.id
                elif comp.type == "capacitor":
                    capacitor_id = comp.id
            
            if resistor_id and capacitor_id:
                is_grounded = False
                for p_name in ["p1", "p2"]:
                    for n_id, n in circuit.nets.items():
                        if n_id == net_id: continue # Must be the OTHER pin
                        if any(ep.component_id == capacitor_id and ep.pin_name == p_name for ep in n.endpoints):
                            if n_id in ground_nets:
                                is_grounded = True
                                break
                    if is_grounded: break
                
                if is_grounded:
                    suggestions.append(PatternSuggestion(
                        pattern_id=self.pattern_id,
                        type="INSPECT_NODE",
                        component="",
                        reason=f"Detected an RC Low-Pass Filter configuration at net '{net_id}'. Ensure the cutoff frequency is appropriate.",
                        confidence=0.9,
                        priority=self.priority,
                        target_component_ids=[resistor_id, capacitor_id],
                        metadata={"net_id": net_id, "type": "RC_Filter"}
                    ))
        return suggestions
