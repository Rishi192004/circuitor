import unittest
from src.models.circuit import Circuit
from src.models.component import Component, ComponentTemplate, PinTemplate
from src.models.net import Net, PinConnection
from src.patterns.decoupling_pattern import DecouplingCapacitorPattern

class TestDecouplingCapacitorPattern(unittest.TestCase):
    def setUp(self):
        self.templates = {
            "op_amp": ComponentTemplate(
                id="op_amp", name="Op-Amp", category="ic",
                pins_template=[
                    PinTemplate("in+", "input"), PinTemplate("in-", "input"),
                    PinTemplate("out", "output"), PinTemplate("vcc", "power"),
                    PinTemplate("vee", "power")
                ],
                default_pins=5, property_schema={}
            ),
            "capacitor": ComponentTemplate(
                id="capacitor", name="Capacitor", category="passive",
                pins_template=[PinTemplate("p1", "passive"), PinTemplate("p2", "passive")],
                default_pins=2, property_schema={}
            ),
            "ground": ComponentTemplate(
                id="ground", name="Ground", category="reference",
                pins_template=[PinTemplate("gnd", "passive")],
                default_pins=1, property_schema={}
            )
        }

    def _build_comp(self, comp_id, type_id):
        return Component(id=comp_id, type=type_id, circuit_id="test", properties={}, metadata={})

    def _build_net(self, net_id, endpoints):
        return Net(id=net_id, circuit_id="test", wire_type="signal", endpoints=endpoints, properties={})

    def test_decoupling_missing(self):
        # Op-amp connected to power but NO capacitor
        comps = {
            "U1": self._build_comp("U1", "op_amp"),
            "G1": self._build_comp("G1", "ground")
        }
        nets = {
            "n_vcc": self._build_net("n_vcc", [PinConnection("U1", "vcc")]),
            "n_gnd": self._build_net("n_gnd", [PinConnection("G1", "gnd")])
        }
        circuit = Circuit(id="test", components=comps, nets=nets, component_templates=self.templates)
        
        detector = DecouplingCapacitorPattern()
        suggestions = detector.match(circuit, [])
        
        # Should suggest decoupling for VCC (and VEE if it was there)
        self.assertTrue(any("missing decoupling capacitor on pin 'vcc'" in s.reason for s in suggestions))

    def test_decoupling_present(self):
        # Op-amp connected to power WITH capacitor to ground
        comps = {
            "U1": self._build_comp("U1", "op_amp"),
            "C1": self._build_comp("C1", "capacitor"),
            "G1": self._build_comp("G1", "ground")
        }
        nets = {
            "n_vcc": self._build_net("n_vcc", [PinConnection("U1", "vcc"), PinConnection("C1", "p1")]),
            "n_gnd": self._build_net("n_gnd", [PinConnection("G1", "gnd"), PinConnection("C1", "p2")])
        }
        circuit = Circuit(id="test", components=comps, nets=nets, component_templates=self.templates)
        
        detector = DecouplingCapacitorPattern()
        suggestions = detector.match(circuit, [])
        
        # Should NOT suggest decoupling for VCC
        self.assertFalse(any("pin 'vcc'" in s.reason for s in suggestions))

if __name__ == '__main__':
    unittest.main()
