"""Slot assignment: give every radio a slot ("colour") using as few slots as possible.

All functions here work on the CONFLICT graph: two nodes joined by an edge
must get different slots. Slots are numbered 0, 1, 2, ...

We try three classic greedy methods and keep the best.
"""


def slot_count(slots):
    """How many different slots a schedule uses (the frame length)."""
    return len(set(slots.values())) if slots else 0


# ---------------------------------------------------------------------------
# The basic building block
# ---------------------------------------------------------------------------

def greedy(conflict, order):
    """Visit nodes in the given order. Give each one the lowest slot number
    that none of its conflicting nodes already has."""
    slots = {}
    for node in order:
        taken = {slots[n] for n in conflict.neighbors(node) if n in slots}
        s = 0
        while s in taken:
            s += 1
        slots[node] = s
    return slots


# ---------------------------------------------------------------------------
# Heuristic 1: Largest first
# Idea: the busiest nodes (most conflicts) are the hardest to place,
# so place them first while there is still lots of choice.
# ---------------------------------------------------------------------------

def largest_first(conflict):
    order = sorted(conflict.nodes, key=lambda n: (-conflict.degree(n), n))
    return greedy(conflict, order)


# ---------------------------------------------------------------------------
# Heuristic 2: Smallest last
# Idea: repeatedly pull out the node with the FEWEST conflicts, then
# colour in the reverse of that removal order. Each node, when coloured,
# has few already-coloured neighbours, so it rarely needs a new slot.
# ---------------------------------------------------------------------------

def smallest_last(conflict):
    remaining = conflict.copy()
    removed = []
    while remaining.number_of_nodes():
        node = min(remaining.nodes, key=lambda n: (remaining.degree(n), n))
        removed.append(node)
        remaining.remove_node(node)
    return greedy(conflict, reversed(removed))


# ---------------------------------------------------------------------------
# Heuristic 3: DSATUR (degree of saturation)
# Idea: always colour next the node that is most "boxed in", meaning the
# node whose neighbours already use the most different slots. That node
# has the fewest options left, so deal with it before it runs out.
# ---------------------------------------------------------------------------

def dsatur(conflict):
    slots = {}

    def saturation(node):
        return len({slots[n] for n in conflict.neighbors(node) if n in slots})

    while len(slots) < conflict.number_of_nodes():
        uncoloured = [n for n in conflict.nodes if n not in slots]
        node = max(uncoloured, key=lambda n: (saturation(n), conflict.degree(n)))
        taken = {slots[n] for n in conflict.neighbors(node) if n in slots}
        s = 0
        while s in taken:
            s += 1
        slots[node] = s
    return slots


HEURISTICS = {
    "Largest-First Greedy": largest_first,
    "Smallest-Last Greedy": smallest_last,
    "DSATUR": dsatur,
}
