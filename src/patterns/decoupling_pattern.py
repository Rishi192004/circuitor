from typing import List
from src.models.circuit import Circuit
from src.models.suggestion import PatternSuggestion
from src.patterns.base import Pattern

class DecouplingCapacitorPattern(Pattern):
    """
    Detects active components (like op-amps) and suggests adding decoupling capacitors 
    between power supply pins and Ground.
    """

    @property
    def pattern_id(self) -> str:
        return "DECOUPLING_CAPACITOR"

    @property
    def priority(self) -> int:
        return 40

    def match(self, circuit: Circuit, issues: List) -> List[PatternSuggestion]:
        suggestions = []
        
        # Power supply pin names for common ICs
        POWER_PINS = {"vcc", "vdd", "vs+", "v+", "vee", "vss", "vs-", "v-"}
        
        # Ground net identification
        ground_nets = set()
        for comp_id, comp in circuit.components.items():
            if "ground" in comp.type or "ground" in comp_id.lower():
                for net_id, net in circuit.nets.items():
                    if any(ep.component_id == comp_id for ep in net.endpoints):
                        ground_nets.add(net_id)

        for comp_id, comp in circuit.components.items():
            if comp.type == "op_amp":
                template = circuit.component_templates.get(comp.type)
                if not template: continue
                
                # Check for decoupling on power pins
                for pin in template.pins_template:
                    if pin.name.lower() in POWER_PINS:
                        # Find the net connected to this pin
                        pin_net_id = None
                        for net_id, net in circuit.nets.items():
                            if any(ep.component_id == comp_id and ep.pin_name == pin.name for ep in net.endpoints):
                                pin_net_id = net_id
                                break
                        
                        if not pin_net_id: continue
                        
                        # Check if this net has a capacitor connected to ground
                        has_decoupling = False
                        for net_ep in circuit.nets[pin_net_id].endpoints:
                            if net_ep.component_id == comp_id: continue
                            
                            other_comp = circuit.components.get(net_ep.component_id)
                            if other_comp and other_comp.type == "capacitor":
                                # Check if the other pin of this capacitor is on a ground net
                                for other_pin in ["p1", "p2"]: # Assuming standard capacitor pin names
                                    if other_pin == net_ep.pin_name: continue
                                    
                                    # Find net for the other pin
                                    for g_net_id in ground_nets:
                                        g_net = circuit.nets.get(g_net_id)
                                        if any(ep.component_id == other_comp.id and ep.pin_name == other_pin for ep in g_net.endpoints):
                                            has_decoupling = True
                                            break
                                    if has_decoupling: break
                            if has_decoupling: break
                            
                        if not has_decoupling:
                            suggestions.append(PatternSuggestion(
                                pattern_id=self.pattern_id,
                                type="ADD_COMPONENT",
                                component="capacitor",
                                reason=f"Active component '{comp_id}' missing decoupling capacitor on pin '{pin.name}'. High-frequency noise might cause instability.",
                                confidence=0.85,
                                priority=40,
                                target_component_ids=[comp_id],
                                metadata={
                                    "suggested_value": "100n",
                                    "target_pin": pin.name,
                                    "connect_to": "GND"
                                }
                            ))
                            
        return suggestions
