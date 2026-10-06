"""Run with:  python3 -m pytest -q   (or  python3 tests/test_schedule.py)"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tdma.analysis import verify                           # noqa: E402
from tdma.coloring import HEURISTICS, slot_count           # noqa: E402
from tdma.planner import make_plan                         # noqa: E402
from tdma.topology import build_conflict_graph, build_radio_graph  # noqa: E402


def test_direct_link_gets_different_slots():
    # A <-> B, 300 m apart: must differ.
    plan = make_plan({"A": (0, 0), "B": (300, 0)})
    assert plan.slots["A"] != plan.slots["B"]


def test_hidden_terminal_gets_different_slots():
    # A -> B <- C. A and C are 800 m apart (cannot hear each other)
    # but both reach B, so they must still differ.
    plan = make_plan({"A": (0, 0), "B": (400, 0), "C": (800, 0)})
    assert plan.radio.has_edge("A", "C") is False
    assert plan.slots["A"] != plan.slots["C"]


def test_three_hops_apart_can_reuse_a_slot():
    # A - B - C - D in a line: A and D are 3 hops apart, so reuse is allowed
    # and the minimum frame is 3 slots, not 4.
    plan = make_plan({"A": (0, 0), "B": (400, 0), "C": (800, 0), "D": (1200, 0)})
    assert slot_count(plan.slots) == 3
    assert plan.slots["A"] == plan.slots["D"]


def test_grid_matches_proven_minimum():
    grid = {f"Node_{i*4+j+1:02d}": (j * 300.0, i * 300.0)
            for i in range(4) for j in range(4)}
    plan = make_plan(grid)
    assert slot_count(plan.slots) == 9
    assert plan.proven_optimal
    assert plan.problems == []


def test_verifier_catches_a_bad_schedule():
    radio = build_radio_graph({"A": (0, 0), "B": (400, 0), "C": (800, 0)}, 500)
    bad = {"A": 0, "B": 1, "C": 0}          # A and C clash at B
    assert verify(radio, bad)


def test_isolated_radio_is_fine():
    plan = make_plan({"A": (0, 0), "B": (5000, 5000)})
    assert slot_count(plan.slots) == 1       # far apart: same slot is safe


def test_random_layouts_are_always_conflict_free():
    for seed in range(100):
        r = random.Random(seed)
        nodes = {f"N{i:02d}": (r.uniform(0, 1500), r.uniform(0, 1500))
                 for i in range(16)}
        radio = build_radio_graph(nodes, 500)
        conflict = build_conflict_graph(radio)
        for fn in HEURISTICS.values():
            assert verify(radio, fn(conflict)) == []
        plan = make_plan(nodes, rounds=50, exact_seconds=1)
        assert plan.problems == []
        assert slot_count(plan.slots) >= plan.lower_bound


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok ", name)
