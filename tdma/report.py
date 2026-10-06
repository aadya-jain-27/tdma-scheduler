"""Text report and JSON export."""

import json

from .analysis import reuse_report
from .coloring import slot_count

WIDE = "=" * 64
THIN = "-" * 64


def column_label(name):
    """'Node_07' -> '07'. Falls back to the full name if there is no '_'."""
    return name.rsplit("_", 1)[-1]


def schedule_matrix(plan):
    """Slot x Node table of 1s and 0s. Row = slot, column = node.
    A 1 means "this node transmits in this slot"."""
    names = list(plan.nodes)
    return [[1 if plan.slots[n] == s else 0 for n in names]
            for s in range(slot_count(plan.slots))]


def render(plan):
    names = list(plan.nodes)
    frame = slot_count(plan.slots)
    out = []
    add = out.append

    add(WIDE)
    add("            TDMA TOPOLOGY OPTIMIZATION REPORT")
    add(WIDE)
    add(f"Total Nodes Processed  : {len(names)}")
    add(f"Configured Radio Range : {plan.radio_range:.1f} meters")
    add(f"Radio Links (1-hop)    : {plan.radio.number_of_edges()}")
    add(f"Conflict Pairs (<=2hop): {plan.conflict.number_of_edges()}")
    add(f"Optimized Frame Length : {frame} unique timeslots (Lower is better)")
    add(f"Theoretical Minimum    : {plan.lower_bound} timeslots "
        f"(degree bound {plan.degree_bound}, clique bound {plan.lower_bound})")
    if plan.proven_optimal:
        add("Optimality             : PROVEN OPTIMAL (no schedule can use fewer slots)")
    else:
        add(f"Optimality             : best found, true minimum is between "
            f"{plan.lower_bound} and {frame}")
    add(f"Spatial Reuse Factor   : {len(names) / frame:.2f} nodes per slot")
    add(THIN)

    add("HEURISTIC COMPARISON:")
    add("")
    for name, count in plan.heuristic_results.items():
        tag = "  <- best start" if name == plan.best_heuristic else ""
        add(f" {name:<24}: {count} slots{tag}")
    add(f" {'+ Iterated Greedy':<24}: {plan.improved_slots} slots")
    add(f" {'+ Exact Search':<24}: {frame} slots")
    add(THIN)

    add("NODE -> SLOT ASSIGNMENTS:")
    add("")
    for n in names:
        add(f" {n}: Slot {plan.slots[n]}")
    add("")

    add("STRUCTURAL TDMA SCHEDULE MATRIX (Slot x Node Boolean Matrix):")
    add("")
    header = "Slot \\ Node | " + " | ".join(column_label(n) for n in names)
    add(header)
    add("-" * len(header))
    for s, row in enumerate(schedule_matrix(plan)):
        cells = " | ".join(f"{v:>{len(column_label(n))}}" for v, n in zip(row, names))
        add(f"Slot {s:02d}     | {cells}")
    add("-" * len(header))
    add("")

    add("SPATIAL REUSE (radios sharing a slot, closest pair distance):")
    add("")
    for s, members, closest in reuse_report(plan.radio, plan.slots):
        short = ", ".join(column_label(m) for m in members)
        if len(members) == 1:
            note = "used by one node only"
        elif closest is None:
            note = "never connected, fully safe"
        else:
            note = f"closest pair {closest} hops apart"
        add(f" Slot {s:02d}: [{short}]  {note}")
    add("")

    if plan.problems:
        add("VERIFICATION FAILED:")
        for p in plan.problems:
            add(f"  ! {p}")
    else:
        add("Execution finalized cleanly. Schedule verified conflict-free.")
        add("(Every same-slot pair re-checked: none are 1 or 2 hops apart.)")
    add(WIDE)
    return "\n".join(out)


def to_json(plan):
    """Machine-readable output. Part 2 (the EMANE bridge) reads this file."""
    return json.dumps({
        "radio_range_m": plan.radio_range,
        "frame_slots": slot_count(plan.slots),
        "lower_bound": plan.lower_bound,
        "proven_optimal": plan.proven_optimal,
        "nodes": list(plan.nodes),
        "positions": {n: list(p) for n, p in plan.nodes.items()},
        "node_to_slot": plan.slots,
        "matrix": schedule_matrix(plan),
        "verified": not plan.problems,
    }, indent=2)
