import unittest
from src.models.circuit import Circuit
from src.models.component import Component, ComponentTemplate, PinTemplate
from src.models.net import Net, PinConnection
from src.patterns.LowPassFilterPattern import LowPassFilterPattern

class TestLowPassFilterPattern(unittest.TestCase):
    def setUp(self):
        self.templates = {
            "resistor": ComponentTemplate("resistor", "Resistor", "passive", [PinTemplate("p1", "passive"), PinTemplate("p2", "passive")], 2, {}),
            "capacitor": ComponentTemplate("capacitor", "Capacitor", "passive", [PinTemplate("p1", "passive"), PinTemplate("p2", "passive")], 2, {}),
            "ground": ComponentTemplate("ground", "Ground", "reference", [PinTemplate("gnd", "passive")], 1, {})
        }

    def test_rc_filter_detected(self):
        comps = {
            "R1": Component("R1", "resistor", "test", {}, {}),
            "C1": Component("C1", "capacitor", "test", {}, {}),
            "G1": Component("G1", "ground", "test", {}, {})
        }
        nets = {
            "n_mid": Net("n_mid", "test", "signal", [PinConnection("R1", "p2"), PinConnection("C1", "p1")], {}),
            "n_gnd": Net("n_gnd", "test", "signal", [PinConnection("C1", "p2"), PinConnection("G1", "gnd")], {})
        }
        circuit = Circuit("test", self.templates, comps, nets)
        pattern = LowPassFilterPattern()
        suggestions = pattern.match(circuit, [])
        self.assertEqual(len(suggestions), 1)
        self.assertIn("RC Low-Pass Filter", suggestions[0].reason)

    def test_rc_filter_not_detected_without_ground(self):
        comps = {
            "R1": Component("R1", "resistor", "test", {}, {}),
            "C1": Component("C1", "capacitor", "test", {}, {})
        }
        nets = {
            "n_mid": Net("n_mid", "test", "signal", [PinConnection("R1", "p2"), PinConnection("C1", "p1")], {})
        }
        circuit = Circuit("test", self.templates, comps, nets)
        pattern = LowPassFilterPattern()
        self.assertEqual(len(pattern.match(circuit, [])), 0)

if __name__ == '__main__':
    unittest.main()
