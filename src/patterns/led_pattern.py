"""
led_pattern.py — Detects an LED driven directly from a voltage source without
a current-limiting series resistor.

Heuristic:
  For every LED in the circuit, examine its anode net.
  If that net contains a source component via a "positive-side" pin
  (i.e. NOT a pin whose name suggests it is a return/ground terminal),
  and NO resistor is also on that net, then the LED is driven without
  current limiting → suggest adding a series resistor.

  Source pins are classified as "positive-side" when:
    (a) their pin type is explicitly "output", OR
    (b) the template has no output-typed pins BUT the pin name does NOT
        appear in a known negative-terminal name set (negative, -, gnd, …).

  This two-tier approach works correctly for both production templates
  (which use proper pin types) and unit-test fixtures (which use "passive"
  for all pins but still have meaningful pin names).

Pattern ID : LED_MISSING_RESISTOR
Priority   : 10  (high — safety-relevant)
Confidence : 0.95
"""

import logging
from typing import List, Set

from src.models.circuit import Circuit
from src.models.validation import ValidationIssue
from src.models.suggestion import PatternSuggestion
from src.patterns.base import Pattern

logger = logging.getLogger(__name__)

# Component type / category identifiers
_LED_TYPES: Set[str] = {"led", "light_emitting_diode", "diode_led"}
_LED_CATEGORY = "led"
_SOURCE_CATEGORY = "source"
_RESISTOR_TYPES: Set[str] = {"resistor"}
_RESISTOR_CATEGORY = "passive"

# Standard LED anode pin names (used to restrict scan to the hot side)
_ANODE_NAMES: Set[str] = {"anode", "a", "+"}

# Source pin names that indicate the *return/negative* terminal.
# If a source pin is named any of these it is NOT considered a positive drive.
_NEGATIVE_PIN_NAMES: Set[str] = {
    "negative", "neg", "-", "gnd", "ground", "v-", "vee", "vss",
    "cathode", "k", "ret", "return",
}


def _is_led(comp_type: str, category: str) -> bool:
    return comp_type.lower() in _LED_TYPES or category.lower() == _LED_CATEGORY


def _is_source(category: str) -> bool:
    return category.lower() == _SOURCE_CATEGORY


def _is_resistor(comp_type: str, category: str) -> bool:
    return comp_type.lower() in _RESISTOR_TYPES or category.lower() == _RESISTOR_CATEGORY


def _is_positive_source_endpoint(pin_name: str, output_pins: Set[str]) -> bool:
    """
    Return True if this source endpoint represents the *positive* (driving) side.

    Two-tier decision:
      1. If the template has explicit output-typed pins: only accept those.
      2. Otherwise (fallback for "passive"-only templates): accept the pin
         unless its name is in the known negative-terminal name set.
    """
    pin_lower = pin_name.lower()
    if output_pins:
        # Tier 1: template has typed output pins
        return pin_name in output_pins
    else:
        # Tier 2: fallback — exclude obviously negative pins
        return pin_lower not in _NEGATIVE_PIN_NAMES


class LEDPattern(Pattern):
    """
    Suggests adding a current-limiting resistor when an LED anode is connected
    directly to a voltage source's positive terminal with no resistor in between.
    """

    @property
    def pattern_id(self) -> str:
        return "LED_MISSING_RESISTOR"

    @property
    def priority(self) -> int:
        return 10

    def match(
        self,
        circuit: Circuit,
        validation_issues: List[ValidationIssue],
    ) -> List[PatternSuggestion]:
        suggestions: List[PatternSuggestion] = []

        # Build component metadata: type, category, output_pins set
        comp_meta: dict = {}
        for comp_id, comp in circuit.components.items():
            template = circuit.component_templates.get(comp.type)
            cat = template.category if template else ""
            output_pins: Set[str] = set()
            if template:
                output_pins = {pt.name for pt in template.pins_template if pt.type == "output"}
            comp_meta[comp_id] = {
                "type": comp.type,
                "category": cat,
                "output_pins": output_pins,
            }

        for led_id, meta in comp_meta.items():
            if not _is_led(meta["type"], meta["category"]):
                continue

            # Determine which of this LED's pins are anode-side
            led_comp = circuit.components[led_id]
            led_template = circuit.component_templates.get(led_comp.type)
            led_pin_names: Set[str] = (
                {pt.name for pt in led_template.pins_template} if led_template else set()
            )
            anode_pins = led_pin_names & _ANODE_NAMES
            # Fallback: if no standard anode name found, consider all LED nets
            check_pins = anode_pins if anode_pins else led_pin_names

            # Collect nets where this LED is present via an anode (or fallback) pin
            candidate_net_ids: List[str] = []
            for net_id, net in circuit.nets.items():
                for ep in net.endpoints:
                    if ep.component_id == led_id and (
                        not check_pins or ep.pin_name in check_pins
                    ):
                        candidate_net_ids.append(net_id)
                        break

            for net_id in candidate_net_ids:
                net = circuit.nets[net_id]

                # Identify sources that appear on this net via their positive terminal
                source_ids_on_net: List[str] = []
                for ep in net.endpoints:
                    cid = ep.component_id
                    if cid not in comp_meta:
                        continue
                    if not _is_source(comp_meta[cid]["category"]):
                        continue
                    if _is_positive_source_endpoint(ep.pin_name, comp_meta[cid]["output_pins"]):
                        source_ids_on_net.append(cid)

                if not source_ids_on_net:
                    continue  # No positive-side source drive on this net

                # Check whether a resistor is also on this net (= current limiting present)
                endpoint_ids = {ep.component_id for ep in net.endpoints}
                has_resistor = any(
                    _is_resistor(comp_meta[cid]["type"], comp_meta[cid]["category"])
                    for cid in endpoint_ids
                    if cid in comp_meta
                )

                if not has_resistor:
                    logger.debug(
                        "LEDPattern: LED '%s' on net '%s' is directly driven by %s.",
                        led_id, net_id, source_ids_on_net,
                    )
                    suggestions.append(
                        PatternSuggestion(
                            pattern_id=self.pattern_id,
                            type="ADD_COMPONENT",
                            component="resistor",
                            reason=(
                                f"LED '{led_id}' is connected directly to voltage source "
                                f"{source_ids_on_net} on net '{net_id}' without a "
                                "current-limiting resistor. Without it, excessive current "
                                "will destroy the LED."
                            ),
                            confidence=0.95,
                            priority=self.priority,
                            target_component_ids=[led_id] + source_ids_on_net,
                            metadata={
                                "net_id": net_id,
                                "suggested_value": "330",
                                "suggested_unit": "\u03a9",
                            },
                        )
                    )
                    # Only one suggestion per LED
                    break

        return suggestions

    def escalation_condition(self, circuit: Circuit, suggestion: PatternSuggestion) -> bool:
        """
        Escalates LED_MISSING_RESISTOR to an error because driving an LED 
        directly from a source is a physical safety/hardware failure hazard.
        """
        if suggestion.pattern_id == self.pattern_id:
            return True
        return False
