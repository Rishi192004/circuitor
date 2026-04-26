from abc import ABC, abstractmethod
from typing import List
from src.models.circuit import Circuit
from src.models.validation import ValidationIssue
from src.constants.enums import ValidationPhase
from src.graph.algorithms import find_source_cycles

class ValidationRule(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass
        
    @property
    def phase(self) -> ValidationPhase:
        return ValidationPhase.PHYSICS

    @abstractmethod
    def validate(self, circuit: Circuit) -> List[ValidationIssue]:
        pass

class FloatingPinRule(ValidationRule):
    @property
    def name(self) -> str:
        return "Floating Pin Check"
        
    @property
    def phase(self) -> ValidationPhase:
        return ValidationPhase.TOPOLOGY
        
    def validate(self, circuit: Circuit) -> List[ValidationIssue]:
        issues = []
        connected_pins = set()
        for net in circuit.nets.values():
            for endpoint in net.endpoints:
                connected_pins.add(f"{endpoint.component_id}.{endpoint.pin_name}")
                
        for comp_id, comp in circuit.components.items():
            template = circuit.component_templates.get(comp.type)
            if template:
                for pin in template.pins_template:
                    if f"{comp_id}.{pin.name}" not in connected_pins:
                        issues.append(ValidationIssue(
                            error_code="E101",
                            rule_name=self.name,
                            technical_message=f"Pin '{comp_id}.{pin.name}' is disconnected.",
                            user_explanation=f"The '{pin.name}' pin on component '{comp_id}' is floating in the air. Electricity cannot flow through a broken path.",
                            suggested_fix={
                                "action": "wire_pin",
                                "description": f"Draw a wire connecting the '{pin.name}' pin of '{comp_id}' to another component or to ground.",
                                "target_component_id": comp_id,
                                "target_pin_name": pin.name
                            },
                            component_id=comp_id,
                            pin_name=pin.name,
                            severity="error"
                        ))
        return issues

class EmptyNetRule(ValidationRule):
    @property
    def name(self) -> str:
        return "Empty Net Check"
        
    @property
    def phase(self) -> ValidationPhase:
        return ValidationPhase.TOPOLOGY
        
    def validate(self, circuit: Circuit) -> List[ValidationIssue]:
        issues = []
        for net_id, net in circuit.nets.items():
            if len(net.endpoints) < 2:
                issues.append(ValidationIssue(
                    error_code="E102",
                    rule_name=self.name,
                    technical_message=f"Net '{net_id}' has < 2 endpoints.",
                    user_explanation=f"You have drawn a wire ('{net_id}') that doesn't connect two things together. A wire must have at least two ends attached to something to be useful.",
                    suggested_fix={
                        "action": "delete_or_connect",
                        "description": "Either delete this floating wire, or attach its other end to a component pin.",
                        "target_net_id": net_id
                    },
                    net_id=net_id,
                    severity="warning"
                ))
        return issues

class MissingGroundRule(ValidationRule):
    @property
    def name(self) -> str:
        return "Missing Ground Check"
        
    def validate(self, circuit: Circuit) -> List[ValidationIssue]:
        has_ground = False
        for comp in circuit.components.values():
            template = circuit.component_templates.get(comp.type)
            if template and (template.category == "reference" or "ground" in template.id.lower()):
                has_ground = True
                break
                
        if not has_ground:
            return [ValidationIssue(
                error_code="E201",
                rule_name=self.name,
                technical_message="Circuit lacks a 0V reference node.",
                user_explanation="Your circuit doesn't have a Ground! Physical simulators need to know where 'Zero Volts' is in order to calculate the math for the rest of the circuit.",
                suggested_fix={
                    "action": "add_ground",
                    "description": "Open the component library, add a 'Ground' component, and connect it to the negative side of your main power source.",
                    "suggested_component_type": "ground"
                },
                severity="error"
            )]
        return []

class ShortCircuitSourceRule(ValidationRule):
    @property
    def name(self) -> str:
        return "Short Circuit Source Check"
        
    def validate(self, circuit: Circuit) -> List[ValidationIssue]:
        issues = []
        for comp_id, comp in circuit.components.items():
            template = circuit.component_templates.get(comp.type)
            if template and template.category == "source":
                source_nets = {}
                for net_id, net in circuit.nets.items():
                    for endpoint in net.endpoints:
                        if endpoint.component_id == comp_id:
                            if net_id not in source_nets:
                                source_nets[net_id] = []
                            source_nets[net_id].append(endpoint.pin_name)
                
                for net_id, pins in source_nets.items():
                    if len(pins) > 1:
                        issues.append(ValidationIssue(
                            error_code="E301",
                            rule_name=self.name,
                            technical_message=f"Voltage source '{comp_id}' pins {pins} are shorted on net '{net_id}'.",
                            user_explanation=f"DANGER: You have wired the positive and negative sides of '{comp_id}' directly together! This creates a short circuit with zero resistance, causing infinite current.",
                            suggested_fix={
                                "action": "break_short",
                                "description": "Remove the wire connecting the two ends of the source, or add a resistor in between to limit the current.",
                                "target_component_id": comp_id,
                                "target_net_id": net_id,
                                "suggested_component_type": "resistor"
                            },
                            component_id=comp_id,
                            net_id=net_id,
                            severity="error"
                        ))
        return issues

class OutputCollisionRule(ValidationRule):
    @property
    def name(self) -> str:
        return "Output Pin Collision Check"
        
    def validate(self, circuit: Circuit) -> List[ValidationIssue]:
        issues = []
        for net_id, net in circuit.nets.items():
            output_pins = []
            for endpoint in net.endpoints:
                comp = circuit.components.get(endpoint.component_id)
                if comp:
                    template = circuit.component_templates.get(comp.type)
                    if template:
                        for pt in template.pins_template:
                            if pt.name == endpoint.pin_name and pt.type == "output":
                                output_pins.append(f"{endpoint.component_id}.{endpoint.pin_name}")
                                break
            
            if len(output_pins) > 1:
                issues.append(ValidationIssue(
                    error_code="E302",
                    rule_name=self.name,
                    technical_message=f"Output pins {output_pins} shorted together on net '{net_id}'.",
                    user_explanation=f"You have wired multiple 'Output' pins ({', '.join(output_pins)}) directly to each other. If one tries to send High voltage and the other sends Low, they will fight and burn out.",
                    suggested_fix={
                        "action": "separate_outputs",
                        "description": "Never connect two outputs together directly. Connect outputs only to inputs, or use a multiplexer/logic gate if you need to combine their signals.",
                        "target_net_id": net_id
                    },
                    net_id=net_id,
                    severity="error"
                ))
        return issues

class UnpoweredCircuitRule(ValidationRule):
    @property
    def name(self) -> str:
        return "Unpowered Circuit Check"
        
    def validate(self, circuit: Circuit) -> List[ValidationIssue]:
        has_source = False
        for comp in circuit.components.values():
            template = circuit.component_templates.get(comp.type)
            if template and template.category == "source":
                has_source = True
                break
                
        if not has_source:
            return [ValidationIssue(
                error_code="E202",
                rule_name=self.name,
                technical_message="Circuit lacks an active power source.",
                user_explanation="Your circuit does not have a power source (like a battery or voltage supply). Without power, the circuit will do nothing and all voltages will be zero.",
                suggested_fix={
                    "action": "add_source",
                    "description": "Open the component library and add a Voltage Source or Current Source to your circuit.",
                    "suggested_component_type": "voltage_source"
                },
                severity="warning"
            )]
        return []

class ZeroResistanceRule(ValidationRule):
    @property
    def name(self) -> str:
        return "Zero Resistance Check"
        
    @property
    def phase(self) -> ValidationPhase:
        return ValidationPhase.SEMANTICS
        
    def validate(self, circuit: Circuit) -> List[ValidationIssue]:
        issues = []
        for comp_id, comp in circuit.components.items():
            if comp.type == "resistor":
                # Get resistance, default to 0 if missing to trigger the error
                resistance = comp.properties.get("resistance", 0)
                try:
                    res_val = float(resistance)
                except (ValueError, TypeError):
                    res_val = 0
                    
                if res_val <= 0:
                    issues.append(ValidationIssue(
                        error_code="E303",
                        rule_name=self.name,
                        technical_message=f"Resistor '{comp_id}' has zero or invalid resistance ({resistance}).",
                        user_explanation=f"The resistor '{comp_id}' has its resistance set to zero (or an invalid value). A zero-ohm resistor is just a wire and can cause math errors in simulation.",
                        suggested_fix={
                            "action": "edit_property",
                            "description": f"Click on '{comp_id}' and change its 'resistance' property to a positive number (like '1k' or '330').",
                            "target_component_id": comp_id,
                            "property_name": "resistance"
                        },
                        component_id=comp_id,
                        severity="error"
                    ))
        return issues


class VoltageSourceLoopRule(ValidationRule):
    @property
    def name(self) -> str:
        return "Voltage Source Loop Check"
        
    def validate(self, circuit: Circuit) -> List[ValidationIssue]:
        issues = []
        cycles = find_source_cycles(circuit)
        
        for cycle in cycles:
            issues.append(ValidationIssue(
                error_code="E304",
                rule_name=self.name,
                technical_message=f"KVL Violation: Ideal power sources {cycle} form a closed loop.",
                user_explanation=f"You have wired multiple power sources ({', '.join(cycle)}) in a closed loop without any resistors between them. They will fight each other, creating infinite current and crashing the simulator.",
                suggested_fix={
                    "action": "break_loop",
                    "description": "Add a resistor to the loop, or remove one of the power sources.",
                    "target_component_ids": cycle,
                    "suggested_component_type": "resistor"
                },
                component_ids=cycle,
                severity="error"
            ))
        return issues
