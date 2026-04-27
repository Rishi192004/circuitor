"""
tests/patterns/test_opamp_pattern.py
Unit tests for OpAmpPattern.

Coverage:
  - Op-amp with both power rails missing  → 2 suggestions (VCC + VEE)
  - Op-amp with only VCC missing          → 1 suggestion
  - Op-amp fully powered                  → no power suggestion
  - Op-amp with direct feedback           → no feedback suggestion
  - Op-amp with one-hop feedback          → no feedback suggestion
  - Op-amp with no feedback               → OPAMP_MISSING_FEEDBACK suggestion
  - Non-opamp circuit                     → no suggestions
  - Edge: pattern id and type correctness
"""

import unittest
from src.models.circuit import Circuit
from src.models.component import Component, ComponentTemplate, PinTemplate
from src.models.net import Net, PinConnection
from src.patterns.opamp_pattern import OpAmpPattern


# ── Helpers ───────────────────────────────────────────────────────────────────

def _template(type_id, category, pin_names) -> ComponentTemplate:
    return ComponentTemplate(
        id=type_id, name=type_id, category=category,
        pins_template=[PinTemplate(name=p, type="passive") for p in pin_names],
        default_pins=len(pin_names), property_schema={},
    )


def _comp(comp_id, type_id) -> Component:
    return Component(id=comp_id, type=type_id, circuit_id="test", properties={}, metadata={})


def _net(net_id, *endpoints) -> Net:
    return Net(
        id=net_id, circuit_id="test", wire_type="signal",
        endpoints=[PinConnection(c, p) for c, p in endpoints],
        properties={},
    )


def _circuit(templates, comps, nets) -> Circuit:
    return Circuit(
        id="test",
        component_templates=templates,
        components={c.id: c for c in comps},
        nets={n.id: n for n in nets},
    )


# ── Standard templates used across tests ──────────────────────────────────────

OPAMP_TMPL = _template("op_amp", "opamp", ["in+", "in-", "out", "vcc", "vee"])
VSRC_TMPL  = _template("dc_voltage_source", "source", ["positive", "negative"])
RESIS_TMPL = _template("resistor", "passive", ["p1", "p2"])
GND_TMPL   = _template("ground", "reference", ["gnd"])

STD_TEMPLATES = {
    "op_amp": OPAMP_TMPL,
    "dc_voltage_source": VSRC_TMPL,
    "resistor": RESIS_TMPL,
    "ground": GND_TMPL,
}


class TestOpAmpPattern(unittest.TestCase):

    def setUp(self):
        self.pattern = OpAmpPattern()

    # ── Pattern meta ──────────────────────────────────────────────────────────

    def test_pattern_id(self):
        self.assertEqual(self.pattern.pattern_id, "OPAMP_MISSING_POWER")

    # ── Power rail checks ─────────────────────────────────────────────────────

    def test_both_power_rails_missing_fires_two_suggestions(self):
        """VCC and VEE both unconnected → 2 power suggestions."""
        comps = [_comp("U1", "op_amp"), _comp("V1", "dc_voltage_source"), _comp("G1", "ground")]
        nets = [
            _net("n_in", ("V1", "positive"), ("U1", "in+")),
            _net("n_gnd", ("V1", "negative"), ("U1", "in-"), ("G1", "gnd")),
            _net("n_out", ("U1", "out")),  # floating output net (1 endpoint, ok for pattern test)
        ]
        circuit = _circuit(STD_TEMPLATES, comps, nets)
        suggestions = self.pattern.match(circuit, [])
        power_suggestions = [s for s in suggestions if s.pattern_id == "OPAMP_MISSING_POWER"]
        rails = {s.metadata.get("rail") for s in power_suggestions}
        self.assertIn("positive", rails)
        self.assertIn("negative", rails)

    def test_only_vcc_missing_fires_one_power_suggestion(self):
        """VCC missing, VEE connected → only positive rail suggestion."""
        comps = [_comp("U1", "op_amp"), _comp("V1", "dc_voltage_source"), _comp("G1", "ground")]
        nets = [
            _net("n_in",  ("V1", "positive"), ("U1", "in+")),
            _net("n_gnd", ("V1", "negative"), ("U1", "in-"), ("U1", "vee"), ("G1", "gnd")),
            _net("n_out", ("U1", "out")),
        ]
        circuit = _circuit(STD_TEMPLATES, comps, nets)
        suggestions = self.pattern.match(circuit, [])
        power = [s for s in suggestions if s.pattern_id == "OPAMP_MISSING_POWER"]
        self.assertEqual(len(power), 1)
        self.assertEqual(power[0].metadata["rail"], "positive")

    def test_fully_powered_no_power_suggestion(self):
        """Both power pins connected → no power suggestion."""
        comps = [
            _comp("U1", "op_amp"), _comp("V1", "dc_voltage_source"),
            _comp("V2", "dc_voltage_source"), _comp("G1", "ground"),
        ]
        nets = [
            _net("n_vcc",  ("V1", "positive"), ("U1", "vcc")),
            _net("n_vee",  ("V2", "negative"), ("U1", "vee")),
            _net("n_in",   ("V1", "negative"), ("U1", "in+")),
            _net("n_gnd",  ("G1", "gnd"),      ("U1", "in-")),
            _net("n_out",  ("U1", "out")),
        ]
        circuit = _circuit(STD_TEMPLATES, comps, nets)
        suggestions = self.pattern.match(circuit, [])
        power = [s for s in suggestions if s.pattern_id == "OPAMP_MISSING_POWER"]
        self.assertEqual(len(power), 0)

    # ── Feedback checks ───────────────────────────────────────────────────────

    def test_direct_feedback_silent(self):
        """Output directly on same net as inverting input → no feedback suggestion."""
        comps = [_comp("U1", "op_amp"), _comp("V1", "dc_voltage_source"), _comp("G1", "ground")]
        nets = [
            _net("n_vcc",  ("V1", "positive"), ("U1", "vcc")),
            _net("n_vee",  ("V1", "negative"), ("U1", "vee")),
            _net("n_in",   ("V1", "positive"), ("U1", "in+")),
            _net("n_gnd",  ("G1", "gnd"),       ("U1", "in-")),
            # Direct feedback: output and in- share a net
            _net("n_fb",   ("U1", "out"), ("U1", "in-")),
        ]
        circuit = _circuit(STD_TEMPLATES, comps, nets)
        suggestions = self.pattern.match(circuit, [])
        fb = [s for s in suggestions if s.pattern_id == "OPAMP_MISSING_FEEDBACK"]
        self.assertEqual(len(fb), 0)

    def test_one_hop_feedback_silent(self):
        """Output → R1 → in- (one-hop through resistor) → no feedback suggestion."""
        comps = [
            _comp("U1", "op_amp"), _comp("V1", "dc_voltage_source"),
            _comp("R1", "resistor"), _comp("G1", "ground"),
        ]
        nets = [
            _net("n_vcc", ("V1", "positive"), ("U1", "vcc")),
            _net("n_vee", ("V1", "negative"), ("U1", "vee")),
            _net("n_in",  ("V1", "positive"), ("U1", "in+")),
            _net("n_gnd", ("G1", "gnd"),      ("U1", "in-"), ("R1", "p2")),
            _net("n_out", ("U1", "out"),      ("R1", "p1")),  # R1 bridges out → in-
        ]
        circuit = _circuit(STD_TEMPLATES, comps, nets)
        suggestions = self.pattern.match(circuit, [])
        fb = [s for s in suggestions if s.pattern_id == "OPAMP_MISSING_FEEDBACK"]
        self.assertEqual(len(fb), 0)

    def test_missing_feedback_fires(self):
        """Output has no path back to in- → OPAMP_MISSING_FEEDBACK suggestion."""
        comps = [
            _comp("U1", "op_amp"), _comp("V1", "dc_voltage_source"),
            _comp("R1", "resistor"), _comp("G1", "ground"),
        ]
        nets = [
            _net("n_vcc", ("V1", "positive"), ("U1", "vcc")),
            _net("n_vee", ("V1", "negative"), ("U1", "vee")),
            _net("n_in",  ("V1", "positive"), ("U1", "in+")),
            _net("n_gnd", ("G1", "gnd"),      ("U1", "in-")),
            # Output goes somewhere but NOT back to in-
            _net("n_out", ("U1", "out"), ("R1", "p1")),
            _net("n_load",("R1", "p2"), ("G1", "gnd")),
        ]
        circuit = _circuit(STD_TEMPLATES, comps, nets)
        suggestions = self.pattern.match(circuit, [])
        fb = [s for s in suggestions if s.pattern_id == "OPAMP_MISSING_FEEDBACK"]
        self.assertEqual(len(fb), 1)
        self.assertEqual(fb[0].type, "ADD_CONNECTION")

    def test_non_opamp_circuit_silent(self):
        """Circuit with no op-amp → no suggestions at all."""
        templates = {
            "dc_voltage_source": VSRC_TMPL,
            "resistor": RESIS_TMPL,
            "ground": GND_TMPL,
        }
        comps = [
            _comp("V1", "dc_voltage_source"), _comp("R1", "resistor"), _comp("G1", "ground"),
        ]
        nets = [
            _net("n1", ("V1", "positive"), ("R1", "p1")),
            _net("n2", ("R1", "p2"), ("V1", "negative"), ("G1", "gnd")),
        ]
        circuit = _circuit(templates, comps, nets)
        self.assertEqual(len(self.pattern.match(circuit, [])), 0)

    def test_suggestion_confidence_is_reasonable(self):
        """All OpAmp suggestions must have confidence > 0 and ≤ 1."""
        comps = [_comp("U1", "op_amp"), _comp("V1", "dc_voltage_source"), _comp("G1", "ground")]
        nets = [
            _net("n_in",  ("V1", "positive"), ("U1", "in+")),
            _net("n_gnd", ("V1", "negative"), ("U1", "in-"), ("G1", "gnd")),
        ]
        circuit = _circuit(STD_TEMPLATES, comps, nets)
        suggestions = self.pattern.match(circuit, [])
        for s in suggestions:
            self.assertGreater(s.confidence, 0.0)
            self.assertLessEqual(s.confidence, 1.0)


if __name__ == "__main__":
    unittest.main()
