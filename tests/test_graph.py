import unittest

from src.models.circuit import Circuit
from src.models.component import Component, ComponentTemplate, PinTemplate
from src.models.net import Net, PinConnection
from src.graph.builder import GraphBuilder

class TestGraphBuilder(unittest.TestCase):
    def setUp(self):
        # Setup a simple circuit: R1 in series with R2
        templates = {
            "resistor": ComponentTemplate(
                id="resistor",
                name="Resistor",
                category="passive",
                pins_template=[PinTemplate("p1", "passive"), PinTemplate("p2", "passive")],
                default_pins=2,
                property_schema={}
            )
        }
        components = {
            "R1": Component("R1", "resistor", "C1", {"resistance": 100}, {}),
            "R2": Component("R2", "resistor", "C1", {"resistance": 200}, {})
        }
        nets = {
            "n1": Net("n1", "C1", "type_1", [PinConnection("R1", "p2"), PinConnection("R2", "p1")], {})
        }
        self.circuit = Circuit("C1", templates, components, nets)
        
    def test_graph_building(self):
        builder = GraphBuilder(self.circuit)
        adjacency_list = builder.build()
        
        # Check nodes
        self.assertIn("R1.p2", adjacency_list)
        self.assertIn("R2.p1", adjacency_list)
        
        # Check edges
        self.assertIn("R2.p1", adjacency_list["R1.p2"])
        self.assertIn("R1.p2", adjacency_list["R2.p1"])

if __name__ == "__main__":
    unittest.main()
