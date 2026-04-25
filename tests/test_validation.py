import unittest
from src.models.circuit import Circuit
from src.models.component import ComponentTemplate, PinTemplate, Component
from src.models.net import Net, PinConnection
from src.validation.rules import (
    FloatingPinRule, EmptyNetRule, MissingGroundRule, 
    ShortCircuitSourceRule, OutputCollisionRule, 
    UnpoweredCircuitRule, ZeroResistanceRule
)

class TestValidationRules(unittest.TestCase):
    def setUp(self):
        # Create common templates with required fields
        self.templates = {
            "resistor": ComponentTemplate(
                id="resistor", name="Resistor", category="passive",
                pins_template=[PinTemplate("p1", "passive"), PinTemplate("p2", "passive")],
                default_pins=2, property_schema={}
            ),
            "dc_voltage_source": ComponentTemplate(
                id="dc_voltage_source", name="DC Voltage Source", category="source",
                pins_template=[PinTemplate("positive", "output"), PinTemplate("negative", "output")],
                default_pins=2, property_schema={}
            ),
            "ground": ComponentTemplate(
                id="ground", name="Ground", category="reference",
                pins_template=[PinTemplate("gnd", "passive")],
                default_pins=1, property_schema={}
            ),
            "logic_gate": ComponentTemplate(
                id="logic_gate", name="Logic Gate", category="ic",
                pins_template=[PinTemplate("in1", "input"), PinTemplate("out1", "output")],
                default_pins=2, property_schema={}
            )
        }

    def _build_comp(self, comp_id, type_id, props):
        return Component(
            id=comp_id, type=type_id, circuit_id="test",
            properties=props, metadata={}
        )
        
    def _build_net(self, net_id, endpoints):
        return Net(
            id=net_id, circuit_id="test", wire_type="signal",
            endpoints=endpoints, properties={}
        )

    def _build_circuit(self, components, nets):
        return Circuit(
            id="test", 
            components=components, 
            nets=nets, 
            component_templates=self.templates
        )

    def test_floating_pin_rule_pass(self):
        comps = {
            "R1": self._build_comp("R1", "resistor", {"resistance": 1000}),
            "V1": self._build_comp("V1", "dc_voltage_source", {"voltage": 5})
        }
        nets = {
            "n1": self._build_net("n1", [PinConnection("R1", "p1"), PinConnection("V1", "positive")]),
            "n2": self._build_net("n2", [PinConnection("R1", "p2"), PinConnection("V1", "negative")])
        }
        circuit = self._build_circuit(comps, nets)
        issues = FloatingPinRule().validate(circuit)
        self.assertEqual(len(issues), 0)

    def test_floating_pin_rule_fail(self):
        comps = {"R1": self._build_comp("R1", "resistor", {"resistance": 1000})}
        nets = {"n1": self._build_net("n1", [PinConnection("R1", "p1")])} # p2 is floating
        circuit = self._build_circuit(comps, nets)
        issues = FloatingPinRule().validate(circuit)
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].pin_name, "p2")

    def test_empty_net_rule_pass(self):
        nets = {"n1": self._build_net("n1", [PinConnection("R1", "p1"), PinConnection("R2", "p1")])}
        circuit = self._build_circuit({}, nets)
        self.assertEqual(len(EmptyNetRule().validate(circuit)), 0)

    def test_empty_net_rule_fail(self):
        nets = {"n1": self._build_net("n1", [PinConnection("R1", "p1")])} # Only 1 endpoint
        circuit = self._build_circuit({}, nets)
        issues = EmptyNetRule().validate(circuit)
        self.assertEqual(len(issues), 1)

    def test_missing_ground_rule_pass(self):
        comps = {"G1": self._build_comp("G1", "ground", {})}
        circuit = self._build_circuit(comps, {})
        self.assertEqual(len(MissingGroundRule().validate(circuit)), 0)

    def test_missing_ground_rule_fail(self):
        comps = {"R1": self._build_comp("R1", "resistor", {})} # No ground
        circuit = self._build_circuit(comps, {})
        self.assertEqual(len(MissingGroundRule().validate(circuit)), 1)

    def test_short_circuit_source_rule_pass(self):
        comps = {"V1": self._build_comp("V1", "dc_voltage_source", {})}
        nets = {
            "n1": self._build_net("n1", [PinConnection("V1", "positive"), PinConnection("R1", "p1")]),
            "n2": self._build_net("n2", [PinConnection("V1", "negative"), PinConnection("R1", "p2")])
        }
        circuit = self._build_circuit(comps, nets)
        self.assertEqual(len(ShortCircuitSourceRule().validate(circuit)), 0)

    def test_short_circuit_source_rule_fail(self):
        comps = {"V1": self._build_comp("V1", "dc_voltage_source", {})}
        nets = {
            "n1": self._build_net("n1", [PinConnection("V1", "positive"), PinConnection("V1", "negative")])
        }
        circuit = self._build_circuit(comps, nets)
        self.assertEqual(len(ShortCircuitSourceRule().validate(circuit)), 1)

    def test_output_collision_rule_pass(self):
        comps = {"U1": self._build_comp("U1", "logic_gate", {}), "U2": self._build_comp("U2", "logic_gate", {})}
        nets = {
            "n1": self._build_net("n1", [PinConnection("U1", "out1"), PinConnection("U2", "in1")])
        }
        circuit = self._build_circuit(comps, nets)
        self.assertEqual(len(OutputCollisionRule().validate(circuit)), 0)

    def test_output_collision_rule_fail(self):
        comps = {"U1": self._build_comp("U1", "logic_gate", {}), "U2": self._build_comp("U2", "logic_gate", {})}
        nets = {
            "n1": self._build_net("n1", [PinConnection("U1", "out1"), PinConnection("U2", "out1")])
        }
        circuit = self._build_circuit(comps, nets)
        self.assertEqual(len(OutputCollisionRule().validate(circuit)), 1)

    def test_unpowered_circuit_rule_pass(self):
        comps = {"V1": self._build_comp("V1", "dc_voltage_source", {})}
        circuit = self._build_circuit(comps, {})
        self.assertEqual(len(UnpoweredCircuitRule().validate(circuit)), 0)

    def test_unpowered_circuit_rule_fail(self):
        comps = {"R1": self._build_comp("R1", "resistor", {})}
        circuit = self._build_circuit(comps, {})
        self.assertEqual(len(UnpoweredCircuitRule().validate(circuit)), 1)

    def test_zero_resistance_rule_pass(self):
        comps = {"R1": self._build_comp("R1", "resistor", {"resistance": 1000})}
        circuit = self._build_circuit(comps, {})
        self.assertEqual(len(ZeroResistanceRule().validate(circuit)), 0)

    def test_zero_resistance_rule_fail(self):
        # Test 0, missing, and invalid string
        for invalid_val in [0, "0", "invalid", -50]:
            comps = {"R1": self._build_comp("R1", "resistor", {"resistance": invalid_val})}
            circuit = self._build_circuit(comps, {})
            self.assertEqual(len(ZeroResistanceRule().validate(circuit)), 1, f"Failed to catch invalid resistance: {invalid_val}")
        
        # Test completely missing property
        comps2 = {"R1": self._build_comp("R1", "resistor", {})}
        self.assertEqual(len(ZeroResistanceRule().validate(self._build_circuit(comps2, {}))), 1)

if __name__ == '__main__':
    unittest.main()
