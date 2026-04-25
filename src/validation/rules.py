from abc import ABC, abstractmethod
from typing import List
from src.models.circuit import Circuit
from src.models.validation import ValidationIssue

class ValidationRule(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def validate(self, circuit: Circuit) -> List[ValidationIssue]:
        pass

class FloatingPinRule(ValidationRule):
    @property
    def name(self) -> str:
        return "Floating Pin Check"
        
    def validate(self, circuit: Circuit) -> List[ValidationIssue]:
        issues = []
        # Find all connected pins across all nets
        connected_pins = set()
        for net in circuit.nets.values():
            for endpoint in net.endpoints:
                connected_pins.add(f"{endpoint.component_id}.{endpoint.pin_name}")
                
        # Check every component's pins
        for comp_id, comp in circuit.components.items():
            template = circuit.component_templates.get(comp.type)
            if template:
                for pin in template.pins_template:
                    if f"{comp_id}.{pin.name}" not in connected_pins:
                        issues.append(ValidationIssue(
                            rule_name=self.name,
                            message=f"Pin '{pin.name}' on component '{comp_id}' is floating (not connected to any net).",
                            component_id=comp_id,
                            pin_name=pin.name,
                            severity="error"
                        ))
        return issues

class EmptyNetRule(ValidationRule):
    @property
    def name(self) -> str:
        return "Empty Net Check"
        
    def validate(self, circuit: Circuit) -> List[ValidationIssue]:
        issues = []
        for net_id, net in circuit.nets.items():
            if len(net.endpoints) < 2:
                issues.append(ValidationIssue(
                    rule_name=self.name,
                    message=f"Net '{net_id}' has fewer than 2 connections. It does not go anywhere.",
                    severity="error"
                ))
        return issues

class MissingGroundRule(ValidationRule):
    @property
    def name(self) -> str:
        return "Missing Ground Check"
        
    def validate(self, circuit: Circuit) -> List[ValidationIssue]:
        # Check if any component's template has category "reference" or id "ground"
        has_ground = False
        for comp in circuit.components.values():
            template = circuit.component_templates.get(comp.type)
            if template and (template.category == "reference" or "ground" in template.id.lower()):
                has_ground = True
                break
                
        if not has_ground:
            return [ValidationIssue(
                rule_name=self.name,
                message="Circuit is missing a ground reference.",
                severity="error"
            )]
        return []

class ShortCircuitSourceRule(ValidationRule):
    @property
    def name(self) -> str:
        return "Short Circuit Source Check"
        
    def validate(self, circuit: Circuit) -> List[ValidationIssue]:
        issues = []
        # Check all voltage sources
        for comp_id, comp in circuit.components.items():
            template = circuit.component_templates.get(comp.type)
            if template and template.category == "source":
                # Find all nets this component is connected to
                source_nets = {}
                for net_id, net in circuit.nets.items():
                    for endpoint in net.endpoints:
                        if endpoint.component_id == comp_id:
                            if net_id not in source_nets:
                                source_nets[net_id] = []
                            source_nets[net_id].append(endpoint.pin_name)
                
                # Check if multiple pins of this source are in the same net
                for net_id, pins in source_nets.items():
                    if len(pins) > 1:
                        issues.append(ValidationIssue(
                            rule_name=self.name,
                            message=f"Voltage source '{comp_id}' is short-circuited on net '{net_id}'. Pins {pins} are connected together.",
                            component_id=comp_id,
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
                        # Find the pin template
                        for pt in template.pins_template:
                            if pt.name == endpoint.pin_name and pt.type == "output":
                                output_pins.append(f"{endpoint.component_id}.{endpoint.pin_name}")
                                break
            
            if len(output_pins) > 1:
                issues.append(ValidationIssue(
                    rule_name=self.name,
                    message=f"Multiple output pins are connected directly together on net '{net_id}': {output_pins}. This can cause a collision.",
                    severity="error"
                ))
        return issues
