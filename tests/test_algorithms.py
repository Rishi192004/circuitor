import unittest
from src.models.circuit import Circuit
from src.models.component import ComponentTemplate, PinTemplate, Component
from src.models.net import Net, PinConnection
from src.graph.algorithms import find_source_cycles

class TestGraphAlgorithms(unittest.TestCase):
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
            )
        }

    def _build_comp(self, comp_id, type_id):
        return Component(
            id=comp_id, type=type_id, circuit_id="test",
            properties={}, metadata={}
        )
        
    def _build_net(self, net_id, endpoints):
        return Net(
            id=net_id, circuit_id="test", wire_type="signal",
            endpoints=endpoints, properties={}
        )

    def test_find_source_cycles_no_cycles(self):
        comps = {
            "V1": self._build_comp("V1", "dc_voltage_source"),
            "R1": self._build_comp("R1", "resistor")
        }
        nets = {
            "n1": self._build_net("n1", [PinConnection("V1", "positive"), PinConnection("R1", "p1")]),
            "n2": self._build_net("n2", [PinConnection("R1", "p2"), PinConnection("V1", "negative")])
        }
        circuit = Circuit(id="test", components=comps, nets=nets, component_templates=self.templates)
        cycles = find_source_cycles(circuit)
        self.assertEqual(len(cycles), 0)

    def test_find_source_cycles_parallel_loop(self):
        comps = {
            "V1": self._build_comp("V1", "dc_voltage_source"),
            "V2": self._build_comp("V2", "dc_voltage_source")
        }
        nets = {
            "n1": self._build_net("n1", [PinConnection("V1", "positive"), PinConnection("V2", "positive")]),
            "n2": self._build_net("n2", [PinConnection("V1", "negative"), PinConnection("V2", "negative")])
        }
        circuit = Circuit(id="test", components=comps, nets=nets, component_templates=self.templates)
        cycles = find_source_cycles(circuit)
        self.assertEqual(len(cycles), 1)
        self.assertCountEqual(cycles[0], ["V1", "V2"])

    def test_find_source_cycles_triple_loop(self):
        # V1 -> V2 -> V3 -> V1
        comps = {
            "V1": self._build_comp("V1", "dc_voltage_source"),
            "V2": self._build_comp("V2", "dc_voltage_source"),
            "V3": self._build_comp("V3", "dc_voltage_source")
        }
        nets = {
            "n1": self._build_net("n1", [PinConnection("V1", "negative"), PinConnection("V2", "positive")]),
            "n2": self._build_net("n2", [PinConnection("V2", "negative"), PinConnection("V3", "positive")]),
            "n3": self._build_net("n3", [PinConnection("V3", "negative"), PinConnection("V1", "positive")])
        }
        circuit = Circuit(id="test", components=comps, nets=nets, component_templates=self.templates)
        cycles = find_source_cycles(circuit)
        self.assertEqual(len(cycles), 1)
        self.assertCountEqual(cycles[0], ["V1", "V2", "V3"])

if __name__ == '__main__':
    unittest.main()
