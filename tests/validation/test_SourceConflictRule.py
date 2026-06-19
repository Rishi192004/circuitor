import unittest
from src.models.circuit import Circuit
from src.models.component import Component, ComponentTemplate, PinTemplate
from src.models.net import Net, PinConnection
from src.validation.rules.SourceConflictRule import SourceConflictRule

class TestSourceConflictRule(unittest.TestCase):
    def setUp(self):
        self.templates = {
            "dc_voltage_source": ComponentTemplate(
                id="dc_voltage_source", name="Source", category="source",
                pins_template=[PinTemplate("positive", "output"), PinTemplate("negative", "output")],
                default_pins=2, property_schema={}
            )
        }

    def test_source_conflict_pass(self):
        comps = {
            "V1": Component("V1", "dc_voltage_source", "test", {"voltage": 5}, {}),
            "V2": Component("V2", "dc_voltage_source", "test", {"voltage": 5}, {})
        }
        nets = {
            "n1": Net("n1", "test", "signal", [PinConnection("V1", "positive"), PinConnection("V2", "positive")], {})
        }
        circuit = Circuit("test", self.templates, comps, nets)
        rule = SourceConflictRule()
        assert len(rule.validate(circuit)) == 0

    def test_source_conflict_fail(self):
        comps = {
            "V1": Component("V1", "dc_voltage_source", "test", {"voltage": 5}, {}),
            "V2": Component("V2", "dc_voltage_source", "test", {"voltage": 3.3}, {})
        }
        nets = {
            "n1": Net("n1", "test", "signal", [PinConnection("V1", "positive"), PinConnection("V2", "positive")], {})
        }
        circuit = Circuit("test", self.templates, comps, nets)
        rule = SourceConflictRule()
        issues = rule.validate(circuit)
        assert len(issues) == 1
        assert "conflicting voltage sources" in issues[0].technical_message
