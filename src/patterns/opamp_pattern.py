"""
opamp_pattern.py — Detects common op-amp wiring issues.

Two sub-checks are performed:

(A) Missing Power Rails
    An op-amp typically requires both a positive supply (VCC/V+) and a
    negative supply or GND (VEE/V-/GND) connected to its power pins.
    If either is absent, the op-amp will not function.

(B) Missing Feedback Loop
    A basic op-amp amplifier needs the output fed back to the inverting
    input (directly or through a resistor). Without feedback, the op-amp
    operates as an open-loop comparator, which may not be the user's intent.

Heuristic limitations:
  - Power pins are identified by common naming conventions (vcc, vdd, v+, vee,
    vss, v-). Templates that use non-standard naming will not be detected.
  - Feedback detection is a local graph scan: it checks whether the output pin
    and inverting input of the same op-amp share a net (directly or via one hop).

Pattern IDs : OPAMP_MISSING_POWER, OPAMP_MISSING_FEEDBACK
Priority    : 20
Confidence  : 0.90 (power), 0.75 (feedback — heuristic only)
"""

import logging
from typing import List, Set

from src.models.circuit import Circuit
from src.models.validation import ValidationIssue
from src.models.suggestion import PatternSuggestion
from src.patterns.base import Pattern

logger = logging.getLogger(__name__)

_OPAMP_TYPES: Set[str] = {"op_amp", "opamp", "operational_amplifier", "lm741", "lm358"}
_OPAMP_CATEGORY = "opamp"

# Common positive supply pin names (lowercase)
_POSITIVE_SUPPLY_PINS: Set[str] = {"vcc", "vdd", "v+", "vs+", "vsupply", "vpos"}
# Common negative supply pin names (lowercase)
_NEGATIVE_SUPPLY_PINS: Set[str] = {"vee", "vss", "v-", "vs-", "vneg", "gnd", "ground"}
# Common output pin names (lowercase)
_OUTPUT_PINS: Set[str] = {"out", "output", "vout", "vo"}
# Common inverting input pin names (lowercase)
_INVERTING_PINS: Set[str] = {"in-", "inv", "inverting", "in_n", "vin-", "v-in", "-"}


def _is_opamp(comp_type: str, category: str) -> bool:
    return comp_type.lower() in _OPAMP_TYPES or category.lower() == _OPAMP_CATEGORY


def _pin_connected(circuit: Circuit, comp_id: str, pin_name: str) -> bool:
    """Return True if the given component pin appears in at least one net."""
    for net in circuit.nets.values():
        for ep in net.endpoints:
            if ep.component_id == comp_id and ep.pin_name == pin_name:
                return True
    return False


def _find_nets_for_pin(circuit: Circuit, comp_id: str, pin_name: str) -> List[str]:
    """Return IDs of all nets containing comp_id.pin_name."""
    return [
        net_id
        for net_id, net in circuit.nets.items()
        if any(ep.component_id == comp_id and ep.pin_name == pin_name for ep in net.endpoints)
    ]


class OpAmpPattern(Pattern):
    """
    Detects op-amps with missing power supply connections or missing feedback.
    """

    @property
    def pattern_id(self) -> str:
        # Base ID — individual suggestions carry their specific sub-IDs
        return "OPAMP_MISSING_POWER"

    @property
    def priority(self) -> int:
        return 20

    def match(
        self,
        circuit: Circuit,
        validation_issues: List[ValidationIssue],
    ) -> List[PatternSuggestion]:
        suggestions: List[PatternSuggestion] = []

        for comp_id, comp in circuit.components.items():
            template = circuit.component_templates.get(comp.type)
            if template is None:
                continue
            if not _is_opamp(comp.type, template.category):
                continue

            pin_names = {pt.name for pt in template.pins_template}

            # ── (A) Power Rail Check ──────────────────────────────────────────
            positive_pins = [
                p for p in pin_names if p.lower() in _POSITIVE_SUPPLY_PINS
            ]
            negative_pins = [
                p for p in pin_names if p.lower() in _NEGATIVE_SUPPLY_PINS
            ]

            missing_positive = [
                p for p in positive_pins if not _pin_connected(circuit, comp_id, p)
            ]
            missing_negative = [
                p for p in negative_pins if not _pin_connected(circuit, comp_id, p)
            ]

            if missing_positive:
                logger.debug(
                    "OpAmpPattern: '%s' is missing positive supply on pins %s.",
                    comp_id, missing_positive,
                )
                suggestions.append(
                    PatternSuggestion(
                        pattern_id="OPAMP_MISSING_POWER",
                        type="ADD_COMPONENT",
                        component="voltage_source",
                        reason=(
                            f"Op-amp '{comp_id}' has unconnected positive supply "
                            f"pin(s) {missing_positive}. Connect a VCC supply to "
                            "power the op-amp."
                        ),
                        confidence=0.90,
                        priority=self.priority,
                        target_component_ids=[comp_id],
                        metadata={"missing_pins": missing_positive, "rail": "positive"},
                    )
                )

            if missing_negative:
                logger.debug(
                    "OpAmpPattern: '%s' is missing negative supply on pins %s.",
                    comp_id, missing_negative,
                )
                suggestions.append(
                    PatternSuggestion(
                        pattern_id="OPAMP_MISSING_POWER",
                        type="ADD_COMPONENT",
                        component="ground",
                        reason=(
                            f"Op-amp '{comp_id}' has unconnected negative supply "
                            f"pin(s) {missing_negative}. Connect GND or a negative "
                            "supply to complete the power circuit."
                        ),
                        confidence=0.90,
                        priority=self.priority,
                        target_component_ids=[comp_id],
                        metadata={"missing_pins": missing_negative, "rail": "negative"},
                    )
                )

            # ── (B) Feedback Loop Check ───────────────────────────────────────
            output_pins = [p for p in pin_names if p.lower() in _OUTPUT_PINS]
            inverting_pins = [p for p in pin_names if p.lower() in _INVERTING_PINS]

            if not output_pins or not inverting_pins:
                # Template doesn't use standard naming — skip heuristic
                continue

            # Collect all nets touching the output and the inverting input
            out_nets: Set[str] = set()
            for op in output_pins:
                out_nets.update(_find_nets_for_pin(circuit, comp_id, op))

            inv_nets: Set[str] = set()
            for ip in inverting_pins:
                inv_nets.update(_find_nets_for_pin(circuit, comp_id, ip))

            # Direct feedback: output and inverting input share at least one net
            direct_feedback = bool(out_nets & inv_nets)

            # One-hop feedback: a net connected to the output also connects to
            # a component whose other net connects to the inverting input
            one_hop_feedback = False
            if not direct_feedback and out_nets:
                for net_id in out_nets:
                    net = circuit.nets[net_id]
                    intermediate_ids = {
                        ep.component_id for ep in net.endpoints if ep.component_id != comp_id
                    }
                    for mid_id in intermediate_ids:
                        # Check if mid_id also appears in any inverting-input net
                        for inv_net_id in inv_nets:
                            inv_net = circuit.nets[inv_net_id]
                            if any(ep.component_id == mid_id for ep in inv_net.endpoints):
                                one_hop_feedback = True
                                break
                        if one_hop_feedback:
                            break
                    if one_hop_feedback:
                        break

            if not direct_feedback and not one_hop_feedback and out_nets:
                logger.debug(
                    "OpAmpPattern: '%s' appears to lack a feedback connection.",
                    comp_id,
                )
                suggestions.append(
                    PatternSuggestion(
                        pattern_id="OPAMP_MISSING_FEEDBACK",
                        type="ADD_CONNECTION",
                        component="resistor",
                        reason=(
                            f"Op-amp '{comp_id}' output does not appear to be fed back "
                            "to the inverting input. Without feedback the op-amp acts as "
                            "an open-loop comparator. Add a feedback resistor from output "
                            "to inverting input to form a stable amplifier."
                        ),
                        confidence=0.75,
                        priority=self.priority + 5,  # slightly lower than power issues
                        target_component_ids=[comp_id],
                        metadata={
                            "output_pins": output_pins,
                            "inverting_pins": inverting_pins,
                        },
                    )
                )

        return suggestions
