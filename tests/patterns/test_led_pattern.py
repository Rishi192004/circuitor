"""
tests/patterns/test_led_pattern.py
Unit tests for LEDPattern.

Coverage:
  - LED directly on source net   → fires LED_MISSING_RESISTOR
  - LED with series resistor      → no suggestion
  - No LED in circuit             → no suggestion
  - Multiple LEDs, one safe       → only fires for the unsafe one
  - Edge: LED on source + resistor on a different net (no protection on this net)
"""

import unittest
from src.models.circuit import Circuit
from src.models.component import Component, ComponentTemplate, PinTemplate
from src.models.net import Net, PinConnection
from src.patterns.led_pattern import LEDPattern


# ── Helpers ──────────────────────────────────────────────────────────────────

def make_templates(**kwargs) -> dict:
    """Build a template dict from keyword args: name → (category, pins_list)."""
    templates = {}
    for type_id, (cat, pins) in kwargs.items():
        templates[type_id] = ComponentTemplate(
            id=type_id,
            name=type_id,
            category=cat,
            pins_template=[PinTemplate(name=p, type="passive") for p in pins],
            default_pins=len(pins),
            property_schema={},
        )
    return templates


def make_comp(comp_id: str, type_id: str, props: dict = None) -> Component:
    return Component(
        id=comp_id, type=type_id, circuit_id="test",
        properties=props or {}, metadata={},
    )


def make_net(net_id: str, *endpoints: tuple) -> Net:
    return Net(
        id=net_id, circuit_id="test", wire_type="signal",
        endpoints=[PinConnection(component_id=c, pin_name=p) for c, p in endpoints],
        properties={},
    )


def build_circuit(templates, components, nets) -> Circuit:
    circuit = Circuit(
        id="test",
        component_templates=templates,
        components={c.id: c for c in components},
        nets={n.id: n for n in nets},
    )
    return circuit


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestLEDPattern(unittest.TestCase):

    def setUp(self):
        self.pattern = LEDPattern()
        self.templates = make_templates(
            led=("led", ["anode", "cathode"]),
            dc_voltage_source=("source", ["positive", "negative"]),
            resistor=("passive", ["p1", "p2"]),
            ground=("reference", ["gnd"]),
        )

    def test_pattern_id(self):
        self.assertEqual(self.pattern.pattern_id, "LED_MISSING_RESISTOR")

    def test_priority_is_low_number(self):
        """High-severity patterns must have a low priority number."""
        self.assertLessEqual(self.pattern.priority, 20)

    def test_led_directly_on_source_fires(self):
        """LED anode on the same net as a source output → suggestion fired."""
        comps = [
            make_comp("V1", "dc_voltage_source"),
            make_comp("D1", "led"),
            make_comp("G1", "ground"),
        ]
        nets = [
            make_net("n1", ("V1", "positive"), ("D1", "anode")),
            make_net("n2", ("D1", "cathode"), ("V1", "negative"), ("G1", "gnd")),
        ]
        circuit = build_circuit(self.templates, comps, nets)
        suggestions = self.pattern.match(circuit, [])
        self.assertEqual(len(suggestions), 1)
        s = suggestions[0]
        self.assertEqual(s.pattern_id, "LED_MISSING_RESISTOR")
        self.assertEqual(s.type, "ADD_COMPONENT")
        self.assertEqual(s.component, "resistor")
        self.assertIn("D1", s.target_component_ids)
        self.assertGreater(s.confidence, 0.0)

    def test_led_with_series_resistor_silent(self):
        """LED connected via resistor → no suggestion."""
        comps = [
            make_comp("V1", "dc_voltage_source"),
            make_comp("R1", "resistor", {"resistance": "330"}),
            make_comp("D1", "led"),
            make_comp("G1", "ground"),
        ]
        nets = [
            make_net("n1", ("V1", "positive"), ("R1", "p1")),
            make_net("n2", ("R1", "p2"), ("D1", "anode")),
            make_net("n3", ("D1", "cathode"), ("V1", "negative"), ("G1", "gnd")),
        ]
        circuit = build_circuit(self.templates, comps, nets)
        suggestions = self.pattern.match(circuit, [])
        self.assertEqual(len(suggestions), 0)

    def test_no_led_in_circuit_silent(self):
        """No LED → no suggestion."""
        comps = [
            make_comp("V1", "dc_voltage_source"),
            make_comp("R1", "resistor", {"resistance": "1000"}),
            make_comp("G1", "ground"),
        ]
        nets = [
            make_net("n1", ("V1", "positive"), ("R1", "p1")),
            make_net("n2", ("R1", "p2"), ("V1", "negative"), ("G1", "gnd")),
        ]
        circuit = build_circuit(self.templates, comps, nets)
        self.assertEqual(len(self.pattern.match(circuit, [])), 0)

    def test_multiple_leds_only_unsafe_fires(self):
        """Two LEDs: D1 protected by resistor, D2 not. Only D2 triggers."""
        comps = [
            make_comp("V1", "dc_voltage_source"),
            make_comp("R1", "resistor", {"resistance": "330"}),
            make_comp("D1", "led"),
            make_comp("D2", "led"),
            make_comp("G1", "ground"),
        ]
        nets = [
            # D1 path: V1 → R1 → D1 → GND  (safe)
            make_net("n1", ("V1", "positive"), ("R1", "p1")),
            make_net("n2", ("R1", "p2"), ("D1", "anode")),
            make_net("n3", ("D1", "cathode"), ("G1", "gnd")),
            # D2 path: V1 → D2 → GND  (unsafe)
            make_net("n4", ("V1", "positive"), ("D2", "anode")),
            make_net("n5", ("D2", "cathode"), ("V1", "negative")),
        ]
        circuit = build_circuit(self.templates, comps, nets)
        suggestions = self.pattern.match(circuit, [])
        fired_ids = {c for s in suggestions for c in s.target_component_ids}
        self.assertIn("D2", fired_ids)
        self.assertNotIn("D1", fired_ids)

    def test_empty_circuit_silent(self):
        circuit = build_circuit(self.templates, [], [])
        self.assertEqual(len(self.pattern.match(circuit, [])), 0)

    def test_suggestion_metadata_contains_net_id(self):
        """Suggestion metadata must include which net triggered the pattern."""
        comps = [
            make_comp("V1", "dc_voltage_source"),
            make_comp("D1", "led"),
            make_comp("G1", "ground"),
        ]
        nets = [
            make_net("hot_net", ("V1", "positive"), ("D1", "anode")),
            make_net("n2", ("D1", "cathode"), ("V1", "negative"), ("G1", "gnd")),
        ]
        circuit = build_circuit(self.templates, comps, nets)
        suggestions = self.pattern.match(circuit, [])
        self.assertIn("net_id", suggestions[0].metadata)


if __name__ == "__main__":
    unittest.main()
