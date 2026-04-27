"""
tests/patterns/test_voltage_divider_pattern.py
Unit tests for VoltageDividerPattern.

Coverage:
  - Two resistors in series across source+GND, midpoint unused → fires
  - Two resistors in series, midpoint connected to a load → silent
  - Only one resistor (no divider) → silent
  - No source present → silent
  - No ground present → silent
  - Valid circuit with no resistors → silent
  - Metadata contains midpoint_net_id
  - Suggestion type is INSPECT_NODE
"""

import unittest
from src.models.circuit import Circuit
from src.models.component import Component, ComponentTemplate, PinTemplate
from src.models.net import Net, PinConnection
from src.patterns.voltage_divider_pattern import VoltageDividerPattern


# ── Helpers ───────────────────────────────────────────────────────────────────

def _tmpl(type_id, category, pins):
    return ComponentTemplate(
        id=type_id, name=type_id, category=category,
        pins_template=[PinTemplate(name=p, type="passive") for p in pins],
        default_pins=len(pins), property_schema={},
    )


def _comp(cid, type_id, props=None):
    return Component(id=cid, type=type_id, circuit_id="test", properties=props or {}, metadata={})


def _net(nid, *eps):
    return Net(
        id=nid, circuit_id="test", wire_type="signal",
        endpoints=[PinConnection(c, p) for c, p in eps],
        properties={},
    )


def _circuit(templates, comps, nets):
    return Circuit(
        id="test", component_templates=templates,
        components={c.id: c for c in comps},
        nets={n.id: n for n in nets},
    )


TEMPLATES = {
    "dc_voltage_source": _tmpl("dc_voltage_source", "source", ["positive", "negative"]),
    "resistor":          _tmpl("resistor", "passive", ["p1", "p2"]),
    "ground":            _tmpl("ground", "reference", ["gnd"]),
    "led":               _tmpl("led", "led", ["anode", "cathode"]),
}


class TestVoltageDividerPattern(unittest.TestCase):

    def setUp(self):
        self.pattern = VoltageDividerPattern()

    # ── Pattern meta ──────────────────────────────────────────────────────────

    def test_pattern_id(self):
        self.assertEqual(self.pattern.pattern_id, "VOLTAGE_DIVIDER_UNUSED_OUTPUT")

    def test_priority(self):
        self.assertGreater(self.pattern.priority, 20)  # less urgent than power issues

    # ── Core detection ────────────────────────────────────────────────────────

    def _divider_circuit(self, extra_on_mid=None):
        """
        Build a canonical voltage divider: V1 → R1 → mid_node → R2 → GND.
        Optionally add components to the midpoint net.
        """
        comps = [
            _comp("V1", "dc_voltage_source", {"voltage": "10"}),
            _comp("R1", "resistor", {"resistance": "10000"}),
            _comp("R2", "resistor", {"resistance": "10000"}),
            _comp("G1", "ground"),
        ]
        mid_eps = [("R1", "p2"), ("R2", "p1")]
        if extra_on_mid:
            mid_eps.extend(extra_on_mid)

        nets = [
            _net("high_net", ("V1", "positive"), ("R1", "p1")),
            _net("mid_net",  *mid_eps),
            _net("low_net",  ("R2", "p2"), ("V1", "negative"), ("G1", "gnd")),
        ]
        return _circuit(TEMPLATES, comps, nets)

    def test_unused_midpoint_fires(self):
        """Classic divider with unused midpoint → suggestion fired."""
        circuit = self._divider_circuit()
        suggestions = self.pattern.match(circuit, [])
        self.assertEqual(len(suggestions), 1)
        s = suggestions[0]
        self.assertEqual(s.pattern_id, "VOLTAGE_DIVIDER_UNUSED_OUTPUT")
        self.assertEqual(s.type, "INSPECT_NODE")
        self.assertIn("R1", s.target_component_ids)
        self.assertIn("R2", s.target_component_ids)

    def test_midpoint_in_use_silent(self):
        """Midpoint already connected to a load (LED cathode) → no suggestion."""
        circuit = self._divider_circuit(extra_on_mid=[("D1", "anode")])
        # Add the LED to the circuit components/templates
        circuit.components["D1"] = _comp("D1", "led")
        suggestions = self.pattern.match(circuit, [])
        self.assertEqual(len(suggestions), 0)

    def test_single_resistor_no_divider(self):
        """Only one resistor → cannot form a divider → silent."""
        comps = [_comp("V1", "dc_voltage_source"), _comp("R1", "resistor"), _comp("G1", "ground")]
        nets = [
            _net("n1", ("V1", "positive"), ("R1", "p1")),
            _net("n2", ("R1", "p2"), ("V1", "negative"), ("G1", "gnd")),
        ]
        circuit = _circuit(TEMPLATES, comps, nets)
        self.assertEqual(len(self.pattern.match(circuit, [])), 0)

    def test_no_source_silent(self):
        """Divider topology but no voltage source → no suggestion."""
        comps = [_comp("R1", "resistor"), _comp("R2", "resistor"), _comp("G1", "ground")]
        nets = [
            _net("n1", ("R1", "p1")),  # dangling
            _net("n2", ("R1", "p2"), ("R2", "p1")),
            _net("n3", ("R2", "p2"), ("G1", "gnd")),
        ]
        circuit = _circuit(TEMPLATES, comps, nets)
        self.assertEqual(len(self.pattern.match(circuit, [])), 0)

    def test_no_ground_silent(self):
        """Two resistors on a source with no GND → pattern should not fire."""
        comps = [_comp("V1", "dc_voltage_source"), _comp("R1", "resistor"), _comp("R2", "resistor")]
        nets = [
            _net("n1", ("V1", "positive"), ("R1", "p1")),
            _net("n2", ("R1", "p2"), ("R2", "p1")),
            _net("n3", ("R2", "p2"), ("V1", "negative")),
        ]
        circuit = _circuit(TEMPLATES, comps, nets)
        self.assertEqual(len(self.pattern.match(circuit, [])), 0)

    def test_empty_circuit_silent(self):
        circuit = _circuit(TEMPLATES, [], [])
        self.assertEqual(len(self.pattern.match(circuit, [])), 0)

    # ── Metadata / quality assertions ─────────────────────────────────────────

    def test_suggestion_contains_midpoint_net_id(self):
        """Metadata must include midpoint_net_id for frontend wiring."""
        circuit = self._divider_circuit()
        suggestions = self.pattern.match(circuit, [])
        self.assertIn("midpoint_net_id", suggestions[0].metadata)
        self.assertEqual(suggestions[0].metadata["midpoint_net_id"], "mid_net")

    def test_no_duplicate_suggestions_for_same_pair(self):
        """Pattern must deduplicate; same resistor pair should not fire twice."""
        circuit = self._divider_circuit()
        suggestions = self.pattern.match(circuit, [])
        # Only one unique (R1, R2) pair — exactly one suggestion
        self.assertEqual(len(suggestions), 1)

    def test_confidence_in_bounds(self):
        circuit = self._divider_circuit()
        suggestions = self.pattern.match(circuit, [])
        s = suggestions[0]
        self.assertGreater(s.confidence, 0.0)
        self.assertLessEqual(s.confidence, 1.0)


if __name__ == "__main__":
    unittest.main()
