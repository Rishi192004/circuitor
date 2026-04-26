import unittest
from src.models.circuit import Circuit
from src.models.component import ComponentTemplate, PinTemplate, Component
from src.models.net import Net, PinConnection
from src.models.pipeline import PipelineResult
from src.models.validation import ValidationIssue
from src.parser.normalizer import ValueNormalizer
from src.graph.builder import GraphBuilder
from src.validation.validator import CircuitValidator
from src.validation.rules import (
    FloatingPinRule, EmptyNetRule, MissingGroundRule,
    ShortCircuitSourceRule, OutputCollisionRule,
    UnpoweredCircuitRule, ZeroResistanceRule,
    VoltageSourceLoopRule
)


class TestPipelineResult(unittest.TestCase):
    """Tests the structured API response envelope and null-filtering."""

    def test_pipeline_result_to_dict_structure(self):
        """Verify PipelineResult.to_dict() returns all expected top-level keys."""
        result = PipelineResult(
            status="success",
            circuit_id="test_circuit",
            phase_reached="ALL_PASSED",
            issues=[],
            graph={"R1.p1": ["V1.positive"]},
            metadata={"rules_run": 8}
        )
        d = result.to_dict()
        self.assertEqual(d["status"], "success")
        self.assertEqual(d["circuit_id"], "test_circuit")
        self.assertEqual(d["phase_reached"], "ALL_PASSED")
        self.assertEqual(d["issues_count"], 0)
        self.assertIsInstance(d["issues"], list)
        self.assertIsInstance(d["graph"], dict)
        self.assertEqual(d["metadata"]["rules_run"], 8)

    def test_validation_issue_null_filtering(self):
        """Verify that to_dict() does NOT emit null target fields."""
        issue = ValidationIssue(
            error_code="E201",
            rule_name="Missing Ground Check",
            technical_message="Circuit lacks a 0V reference node.",
            user_explanation="No ground.",
            suggested_fix={"action": "add_ground"},
            severity="error"
            # component_id, pin_name, net_id, component_ids, net_ids are all None
        )
        d = issue.to_dict()
        target = d["target"]
        self.assertEqual(target["type"], "global")
        # None fields must NOT be present
        self.assertNotIn("component_id", target)
        self.assertNotIn("component_ids", target)
        self.assertNotIn("pin_name", target)
        self.assertNotIn("net_id", target)
        self.assertNotIn("net_ids", target)

    def test_validation_issue_component_target(self):
        """Verify component-level issue emits only the relevant target fields."""
        issue = ValidationIssue(
            error_code="E101",
            rule_name="Floating Pin Check",
            technical_message="Pin 'R1.p2' is disconnected.",
            user_explanation="Floating pin.",
            suggested_fix={"action": "wire_pin"},
            component_id="R1",
            pin_name="p2",
            severity="error"
        )
        d = issue.to_dict()
        target = d["target"]
        self.assertEqual(target["type"], "component")
        self.assertEqual(target["component_id"], "R1")
        self.assertEqual(target["pin_name"], "p2")
        self.assertNotIn("net_id", target)
        self.assertNotIn("component_ids", target)

    def test_validation_issue_multiple_target(self):
        """Verify multi-component issue emits component_ids."""
        issue = ValidationIssue(
            error_code="E304",
            rule_name="Voltage Source Loop Check",
            technical_message="KVL Violation.",
            user_explanation="Loop detected.",
            suggested_fix={"action": "break_loop"},
            component_ids=["V1", "V2"],
            severity="error"
        )
        d = issue.to_dict()
        target = d["target"]
        self.assertEqual(target["type"], "multiple")
        self.assertEqual(target["component_ids"], ["V1", "V2"])
        self.assertNotIn("component_id", target)


class TestPhaseOrchestration(unittest.TestCase):
    """Tests that the orchestrator halts correctly and reports the right phase."""

    def setUp(self):
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
            )
        }

    def _build_comp(self, comp_id, type_id, props=None):
        return Component(
            id=comp_id, type=type_id, circuit_id="test",
            properties=props or {}, metadata={}
        )

    def _build_net(self, net_id, endpoints):
        return Net(
            id=net_id, circuit_id="test", wire_type="signal",
            endpoints=endpoints, properties={}
        )

    def test_topology_halt_skips_physics(self):
        """If a floating pin exists (TOPOLOGY error), PHYSICS rules should NOT run."""
        comps = {
            "R1": self._build_comp("R1", "resistor", {"resistance": 1000})
        }
        # Only connect p1, leave p2 floating
        nets = {
            "n1": self._build_net("n1", [PinConnection("R1", "p1")])
        }
        circuit = Circuit(id="test", components=comps, nets=nets, component_templates=self.templates)

        validator = CircuitValidator(circuit)
        validator.add_rule(FloatingPinRule())
        validator.add_rule(EmptyNetRule())
        validator.add_rule(MissingGroundRule())  # PHYSICS — should NOT run

        issues, phase_reached = validator.validate()
        self.assertEqual(phase_reached, "TOPOLOGY")
        # MissingGroundRule would add 1 more issue, but it should be blocked
        error_codes = [i.error_code for i in issues]
        self.assertIn("E101", error_codes)
        self.assertNotIn("E201", error_codes)

    def test_all_passed_when_clean(self):
        """A clean circuit should reach ALL_PASSED."""
        comps = {
            "V1": self._build_comp("V1", "dc_voltage_source", {"voltage": 5}),
            "R1": self._build_comp("R1", "resistor", {"resistance": 1000}),
            "G1": self._build_comp("G1", "ground", {})
        }
        nets = {
            "n1": self._build_net("n1", [PinConnection("V1", "positive"), PinConnection("R1", "p1")]),
            "n2": self._build_net("n2", [PinConnection("R1", "p2"), PinConnection("V1", "negative"), PinConnection("G1", "gnd")])
        }
        circuit = Circuit(id="test", components=comps, nets=nets, component_templates=self.templates)

        validator = CircuitValidator(circuit)
        validator.add_rule(FloatingPinRule())
        validator.add_rule(EmptyNetRule())
        validator.add_rule(MissingGroundRule())
        validator.add_rule(ShortCircuitSourceRule())
        validator.add_rule(ZeroResistanceRule())

        issues, phase_reached = validator.validate()
        self.assertEqual(len(issues), 0)
        self.assertEqual(phase_reached, "ALL_PASSED")


if __name__ == '__main__':
    unittest.main()
