import unittest
from src.models.circuit import Circuit
from src.models.component import Component, ComponentTemplate, PinTemplate
from src.models.net import Net, PinConnection
from src.hints.floating_input_hint import FloatingOpAmpInputHint

class TestFloatingOpAmpInputHint(unittest.TestCase):
    def setUp(self):
        self.templates = {
            "op_amp": ComponentTemplate(
                id="op_amp", name="Op-Amp", category="ic",
                pins_template=[
                    PinTemplate("non_inverting", "input"), 
                    PinTemplate("inverting", "input"),
                    PinTemplate("out", "output")
                ],
                default_pins=3, property_schema={}
            )
        }

    def _build_comp(self, comp_id, type_id):
        return Component(id=comp_id, type=type_id, circuit_id="test", properties={}, metadata={})

    def _build_net(self, net_id, endpoints):
        return Net(id=net_id, circuit_id="test", wire_type="signal", endpoints=endpoints, properties={})

    def test_floating_input_detected(self):
        # Op-amp with non_inverting pin NOT connected to any net
        comps = {"U1": self._build_comp("U1", "op_amp")}
        # Only connecting inverting pin
        nets = {"n1": self._build_net("n1", [PinConnection("U1", "inverting")])}
        circuit = Circuit(id="test", components=comps, nets=nets, component_templates=self.templates)
        
        hint = FloatingOpAmpInputHint()
        results = hint.check(circuit)
        
        self.assertTrue(any("floating input pin 'non_inverting'" in h.message for h in results))

    def test_floating_input_not_detected(self):
        # All inputs connected
        comps = {"U1": self._build_comp("U1", "op_amp")}
        nets = {
            "n1": self._build_net("n1", [PinConnection("U1", "non_inverting")]),
            "n2": self._build_net("n2", [PinConnection("U1", "inverting")])
        }
        circuit = Circuit(id="test", components=comps, nets=nets, component_templates=self.templates)
        
        hint = FloatingOpAmpInputHint()
        results = hint.check(circuit)
        
        self.assertEqual(len(results), 0)

if __name__ == '__main__':
    unittest.main()
