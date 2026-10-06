"""The whole pipeline in one place: coordinates in, checked schedule out."""

from dataclasses import dataclass, field

from .analysis import lower_bound, verify
from .coloring import HEURISTICS, exact_improve, iterated_greedy, slot_count
from .topology import build_conflict_graph, build_radio_graph


@dataclass
class Plan:
    nodes: dict                 # name -> (x, y)
    radio_range: float
    radio: object               # networkx graph: who can hear whom
    conflict: object            # networkx graph: who must not share a slot
    slots: dict                 # name -> slot number (the final answer)
    heuristic_results: dict     # heuristic name -> slot count
    best_heuristic: str
    improved_slots: int         # slot count after iterated greedy
    degree_bound: int
    lower_bound: int
    proven_optimal: bool
    problems: list = field(default_factory=list)


def make_plan(nodes, radio_range=500.0, rounds=300, seed=0, exact_seconds=5.0):
    radio = build_radio_graph(nodes, radio_range)
    conflict = build_conflict_graph(radio)

    # 1. Run every heuristic and keep the one with the fewest slots.
    results = {name: fn(conflict) for name, fn in HEURISTICS.items()}
    best_name = min(results, key=lambda name: slot_count(results[name]))
    best = results[best_name]

    # 2. Try to squeeze it further with iterated greedy.
    best = iterated_greedy(conflict, best, rounds=rounds, seed=seed)
    improved = slot_count(best)

    # 3. Work out the theoretical minimum and, if there is a gap, try the
    #    exact search to close it (or prove it cannot be closed).
    degree_bound, bound = lower_bound(radio, conflict)
    best, optimal = exact_improve(conflict, best, bound, exact_seconds)

    # 4. Cosmetic: renumber slots in node order so Node_01 gets Slot 0,
    #    the next new slot seen is Slot 1, and so on. Same schedule, tidier.
    renumber = {}
    for name in nodes:
        renumber.setdefault(best[name], len(renumber))
    best = {name: renumber[best[name]] for name in nodes}

    # 5. Independent safety check of the final answer.
    problems = verify(radio, best)

    return Plan(
        nodes=nodes,
        radio_range=radio_range,
        radio=radio,
        conflict=conflict,
        slots=best,
        heuristic_results={n: slot_count(s) for n, s in results.items()},
        best_heuristic=best_name,
        improved_slots=improved,
        degree_bound=degree_bound,
        lower_bound=bound,
        proven_optimal=optimal,
        problems=problems,
    )
