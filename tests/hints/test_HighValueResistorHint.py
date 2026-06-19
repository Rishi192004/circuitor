import unittest
from src.models.circuit import Circuit
from src.models.component import Component, ComponentTemplate, PinTemplate
from src.hints.HighValueResistorHint import HighValueResistorHint

class TestHighValueResistorHint(unittest.TestCase):
    def setUp(self):
        self.templates = {
            "resistor": ComponentTemplate("resistor", "Resistor", "passive", [PinTemplate("p1", "passive"), PinTemplate("p2", "passive")], 2, {})
        }

    def test_high_value_resistor_detected(self):
        comps = {"R1": Component("R1", "resistor", "test", {"resistance": "2.2M"}, {})}
        circuit = Circuit("test", self.templates, comps, {})
        hint = HighValueResistorHint()
        results = hint.check(circuit)
        self.assertEqual(len(results), 1)
        self.assertIn("noise", results[0].message)

    def test_standard_resistor_no_hint(self):
        comps = {"R1": Component("R1", "resistor", "test", {"resistance": "1k"}, {})}
        circuit = Circuit("test", self.templates, comps, {})
        hint = HighValueResistorHint()
        self.assertEqual(len(hint.check(circuit)), 0)

if __name__ == '__main__':
    unittest.main()
