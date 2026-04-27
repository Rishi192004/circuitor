"""
voltage_divider_pattern.py — Detects a voltage divider topology (two resistors
in series across a voltage source and ground) and suggests using the midpoint
as an output node.

Heuristic:
  A voltage divider exists when:
    1. A voltage source is present.
    2. Two resistors (R_top, R_bot) form a series chain: source+ → R_top → node → R_bot → GND.
    3. The intermediate node (junction of R_top and R_bot) is NOT explicitly
       used as an output connection to any other component.

  If condition 3 holds, the user may have forgotten to wire the output.

Pattern ID : VOLTAGE_DIVIDER_UNUSED_OUTPUT
Priority   : 30
Confidence : 0.80
"""

import logging
from typing import Dict, List, Optional, Set, Tuple

from src.models.circuit import Circuit
from src.models.validation import ValidationIssue
from src.models.suggestion import PatternSuggestion
from src.patterns.base import Pattern

logger = logging.getLogger(__name__)

_SOURCE_CATEGORY = "source"
_REFERENCE_CATEGORY = "reference"  # ground
_RESISTOR_TYPES: Set[str] = {"resistor"}
_RESISTOR_CATEGORY = "passive"


def _category(circuit: Circuit, comp_id: str) -> str:
    comp = circuit.components.get(comp_id)
    if comp is None:
        return ""
    template = circuit.component_templates.get(comp.type)
    return template.category if template else ""


def _is_source(circuit: Circuit, comp_id: str) -> bool:
    return _category(circuit, comp_id).lower() == _SOURCE_CATEGORY


def _is_ground(circuit: Circuit, comp_id: str) -> bool:
    cat = _category(circuit, comp_id).lower()
    comp = circuit.components.get(comp_id)
    type_id = comp.type.lower() if comp else ""
    return cat == _reference_category_lower() or "ground" in type_id


def _reference_category_lower() -> str:
    return _REFERENCE_CATEGORY.lower()


def _is_resistor(circuit: Circuit, comp_id: str) -> bool:
    comp = circuit.components.get(comp_id)
    if comp is None:
        return False
    template = circuit.component_templates.get(comp.type)
    cat = template.category if template else ""
    return comp.type.lower() in _RESISTOR_TYPES or cat.lower() == _RESISTOR_CATEGORY


def _nets_for_component(circuit: Circuit, comp_id: str) -> Dict[str, str]:
    """Return {net_id: pin_name} for every net the component is connected to."""
    result = {}
    for net_id, net in circuit.nets.items():
        for ep in net.endpoints:
            if ep.component_id == comp_id:
                result[net_id] = ep.pin_name
    return result


def _other_comps_in_net(circuit: Circuit, net_id: str, exclude: str) -> Set[str]:
    """Return component IDs in net_id, excluding `exclude`."""
    return {
        ep.component_id
        for ep in circuit.nets[net_id].endpoints
        if ep.component_id != exclude
    }


def _net_has_only_two_resistors(circuit: Circuit, net_id: str) -> bool:
    """
    True if this net connects exactly two resistors (the midpoint node of a divider).
    """
    comps = {ep.component_id for ep in circuit.nets[net_id].endpoints}
    return len(comps) == 2 and all(_is_resistor(circuit, c) for c in comps)


class VoltageDividerPattern(Pattern):
    """
    Detects two resistors forming a voltage divider across a source and suggests
    exploiting the midpoint (output node) if it is currently unused.
    """

    @property
    def pattern_id(self) -> str:
        return "VOLTAGE_DIVIDER_UNUSED_OUTPUT"

    @property
    def priority(self) -> int:
        return 30

    def match(
        self,
        circuit: Circuit,
        validation_issues: List[ValidationIssue],
    ) -> List[PatternSuggestion]:
        suggestions: List[PatternSuggestion] = []
        already_suggested: Set[Tuple[str, str]] = set()  # (r_top_id, r_bot_id)

        # Collect resistors once
        resistor_ids = [
            cid for cid in circuit.components if _is_resistor(circuit, cid)
        ]
        # Collect ground component IDs
        ground_ids = {
            cid for cid in circuit.components if _is_ground(circuit, cid)
        }
        # Collect source component IDs
        source_ids = {
            cid for cid in circuit.components if _is_source(circuit, cid)
        }

        if not source_ids or len(resistor_ids) < 2:
            return []

        # For each resistor, look for a series pair forming a divider
        for r_top_id in resistor_ids:
            r_top_nets = _nets_for_component(circuit, r_top_id)  # {net_id: pin_name}

            for net_id, _ in r_top_nets.items():
                net = circuit.nets[net_id]
                endpoint_ids = {ep.component_id for ep in net.endpoints}

                # ── Check if this net is the HIGH side: source + R_top ────────
                # (source output is on the same net as one pin of R_top)
                source_on_net = endpoint_ids & source_ids
                if not source_on_net:
                    continue

                # Find the other net(s) of R_top — the middle node candidate
                for mid_net_id, _ in r_top_nets.items():
                    if mid_net_id == net_id:
                        continue  # skip the high-side net

                    mid_net = circuit.nets[mid_net_id]
                    mid_endpoint_ids = {ep.component_id for ep in mid_net.endpoints}

                    # The middle node should contain R_top and another resistor
                    resistors_on_mid = mid_endpoint_ids & set(resistor_ids)
                    if r_top_id not in resistors_on_mid or len(resistors_on_mid) < 2:
                        continue

                    for r_bot_id in resistors_on_mid:
                        if r_bot_id == r_top_id:
                            continue

                        pair_key = tuple(sorted([r_top_id, r_bot_id]))
                        if pair_key in already_suggested:
                            continue

                        # R_bot must have its other end connected to ground
                        r_bot_nets = _nets_for_component(circuit, r_bot_id)
                        low_side_nets = {n for n in r_bot_nets if n != mid_net_id}

                        gnd_connected = any(
                            any(ep.component_id in ground_ids for ep in circuit.nets[n].endpoints)
                            for n in low_side_nets
                        )
                        if not gnd_connected:
                            continue

                        # ── Divider confirmed ─────────────────────────────────
                        # Check if the mid-point net is used by anything *other*
                        # than the two resistors (= it already has an output load)
                        other_comps = mid_endpoint_ids - {r_top_id, r_bot_id}
                        if other_comps:
                            # Midpoint is already in use — no suggestion needed
                            already_suggested.add(pair_key)
                            continue

                        already_suggested.add(pair_key)
                        logger.debug(
                            "VoltageDividerPattern: Divider detected — "
                            "%s (top) and %s (bot), midpoint net '%s' is unused.",
                            r_top_id, r_bot_id, mid_net_id,
                        )
                        suggestions.append(
                            PatternSuggestion(
                                pattern_id=self.pattern_id,
                                type="INSPECT_NODE",
                                component="",  # no specific component to add
                                reason=(
                                    f"Resistors '{r_top_id}' and '{r_bot_id}' form a "
                                    f"voltage divider across the supply. The midpoint "
                                    f"(net '{mid_net_id}') produces a scaled output "
                                    "voltage but is not connected to anything. "
                                    "Consider wiring the midpoint to a load or output pin."
                                ),
                                confidence=0.80,
                                priority=self.priority,
                                target_component_ids=[r_top_id, r_bot_id],
                                metadata={
                                    "midpoint_net_id": mid_net_id,
                                    "high_side_net_id": net_id,
                                    "source_ids": list(source_on_net),
                                    "ground_ids": list(
                                        {ep.component_id for ep in circuit.nets[next(iter(low_side_nets))].endpoints}
                                        & ground_ids
                                    ),
                                },
                            )
                        )

        return suggestions
