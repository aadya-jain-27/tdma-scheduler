"""Slot assignment: give every radio a slot ("colour") using as few slots as possible.

All functions here work on the CONFLICT graph: two nodes joined by an edge
must get different slots. Slots are numbered 0, 1, 2, ...

We try three classic greedy methods, keep the best, then try to improve it.
Because we only have 16 nodes, we can also run an exact search to check
whether an even smaller schedule exists.
"""

import random
import time
from collections import defaultdict


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


# ---------------------------------------------------------------------------
# Improvement step: Iterated Greedy (Culberson's method)
#
# Take a finished schedule, group the nodes by slot, shuffle the ORDER OF
# THE GROUPS, and run greedy again in that order. Proven fact: this can
# never use MORE slots than before (each group still fits together), and
# it often uses fewer. Repeat many times and keep the best.
# ---------------------------------------------------------------------------

def iterated_greedy(conflict, start, rounds=300, seed=0):
    rng = random.Random(seed)
    best = dict(start)
    current = dict(start)

    for _ in range(rounds):
        groups = defaultdict(list)
        for node, s in current.items():
            groups[s].append(node)
        group_list = list(groups.values())

        # Mix three ways of re-ordering the groups.
        trick = rng.random()
        if trick < 0.4:
            group_list.reverse()
        elif trick < 0.7:
            group_list.sort(key=len, reverse=True)
        else:
            rng.shuffle(group_list)

        order = [node for group in group_list for node in group]
        current = greedy(conflict, order)

        if slot_count(current) < slot_count(best):
            best = dict(current)

    return best


# ---------------------------------------------------------------------------
# Exact check: can it be done with k slots? (backtracking)
#
# Try slots for each node one at a time. If we get stuck, undo the last
# choice and try the next option. This checks every possibility, so if it
# says "no", then k slots is truly impossible. Fine for 16 nodes, too slow
# for thousands, so it has a time limit.
# ---------------------------------------------------------------------------

def fits_in_k_slots(conflict, k, deadline):
    """Return a schedule using at most k slots, or None if impossible.
    Raises TimeoutError if the deadline passes first."""
    slots = {}
    nodes = list(conflict.nodes)

    def pick_next():
        # Same "most boxed in first" rule as DSATUR: fail early, search less.
        uncoloured = [n for n in nodes if n not in slots]
        return max(uncoloured, key=lambda n: (
            len({slots[m] for m in conflict.neighbors(n) if m in slots}),
            conflict.degree(n),
        ))

    def search():
        if time.monotonic() > deadline:
            raise TimeoutError
        if len(slots) == len(nodes):
            return True

        node = pick_next()
        taken = {slots[m] for m in conflict.neighbors(node) if m in slots}

        # Slot numbers are interchangeable, so opening "a new slot" only
        # needs trying once (the next unused number). This removes a huge
        # amount of repeated work.
        highest = max(slots.values(), default=-1)
        for s in range(min(k, highest + 2)):
            if s not in taken:
                slots[node] = s
                if search():
                    return True
                del slots[node]
        return False

    return dict(slots) if search() else None


def exact_improve(conflict, best, lower_bound, seconds):
    """Try to beat `best` with the exact search.

    Returns (schedule, proven_optimal). proven_optimal is True when we know
    no smaller schedule exists, False if we ran out of time.
    """
    if slot_count(best) <= lower_bound:
        return best, True

    deadline = time.monotonic() + seconds
    try:
        k = slot_count(best) - 1
        while k >= lower_bound:
            smaller = fits_in_k_slots(conflict, k, deadline)
            if smaller is None:
                return best, True      # k is impossible, so best is optimal
            best = smaller
            k = slot_count(best) - 1
        return best, True              # reached the lower bound
    except TimeoutError:
        return best, False
