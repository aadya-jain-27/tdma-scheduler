"""Checks on a finished schedule: lower bound, verification, reuse stats.

  lower_bound()  : the fewest slots ANY schedule could possibly use.
  verify()       : an independent collision check that does not trust
                   the conflict graph, it re-measures hop distances.
  reuse_report() : which radios share each slot, and how far apart they are.
"""

from itertools import combinations

import networkx as nx


def lower_bound(radio, conflict):
    """Two ways to prove "you need at least this many slots".

    degree bound: take the busiest radio B. B and all its neighbours must
                  each have a different slot (neighbours of B are 2 hops
                  apart from each other). So slots >= max neighbours + 1.

    clique bound: a "clique" in the conflict graph is a group where every
                  pair clashes, so every member needs its own slot. The
                  biggest such group is a lower bound. It is always at
                  least as strong as the degree bound.
    """
    degree_bound = max((d for _, d in radio.degree()), default=0) + 1
    clique_bound = max((len(c) for c in nx.find_cliques(conflict)), default=0)
    return degree_bound, max(degree_bound, clique_bound)


def verify(radio, slots):
    """Return a list of problems. An empty list means the schedule is safe.

    For every pair of radios sharing a slot, measure the real hop distance
    on the radio graph. 1 or 2 hops means a collision.
    """
    problems = []

    missing = [n for n in radio.nodes if n not in slots]
    if missing:
        problems.append(f"no slot assigned to {', '.join(missing)}")

    hops = dict(nx.all_pairs_shortest_path_length(radio, cutoff=2))
    for a, b in combinations(sorted(slots), 2):
        if slots[a] == slots[b] and b in hops.get(a, {}):
            kind = "direct link" if hops[a][b] == 1 else "hidden terminal"
            problems.append(
                f"{a} and {b} share slot {slots[a]} but are "
                f"{hops[a][b]} hop(s) apart ({kind})"
            )
    return problems


def reuse_report(radio, slots):
    """For each slot: the radios using it and the closest pair's hop distance.

    A distance of 3+ hops (or "never meet" if not connected at all) is what
    spatial reuse looks like: same slot, far enough apart to be safe.
    """
    hops = dict(nx.all_pairs_shortest_path_length(radio))
    rows = []
    for s in sorted(set(slots.values())):
        members = sorted(n for n in slots if slots[n] == s)
        closest = None
        for a, b in combinations(members, 2):
            d = hops[a].get(b)            # None means not connected at all
            if d is not None and (closest is None or d < closest):
                closest = d
        rows.append((s, members, closest))
    return rows
