"""Build the radio graph and the conflict graph from node coordinates.

We build two graphs:

  radio graph    : an edge means "these two radios can hear each other"
                   (they are within radio range).
  conflict graph : an edge means "these two radios must NOT share a slot".
                   That is true when they are 1 hop apart OR 2 hops apart.

The conflict graph is what the maths world calls the "square" of the radio
graph (G squared). Once we have it, distance-2 colouring of the radio graph
becomes plain, normal colouring of the conflict graph.
"""

import json
import math

import networkx as nx


def parse_nodes(text):
    """Read the JSON input, e.g. {"Node_01": [0.0, 0.0], ...}.

    Returns a dict {name: (x, y)} with the names sorted, so the output
    order is always the same no matter how the JSON was written.
    """
    data = json.loads(text)
    if not isinstance(data, dict) or not data:
        raise ValueError("input must be a non-empty JSON object of node -> [x, y]")

    nodes = {}
    for name in sorted(data):
        xy = data[name]
        if not isinstance(xy, (list, tuple)) or len(xy) != 2:
            raise ValueError(f"{name}: expected [x, y], got {xy!r}")
        nodes[name] = (float(xy[0]), float(xy[1]))
    return nodes


def build_radio_graph(nodes, radio_range):
    """Connect every pair of radios that are within radio_range metres."""
    radio = nx.Graph()
    for name, pos in nodes.items():
        radio.add_node(name, pos=pos)

    names = list(nodes)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            distance = math.dist(nodes[a], nodes[b])
            if distance <= radio_range:
                radio.add_edge(a, b, distance=distance)
    return radio


def build_conflict_graph(radio):
    """Connect every pair of radios that would collide in the same slot.

    Rule 1 (distance 1): two neighbours clash directly.
    Rule 2 (distance 2): two radios that share a neighbour B clash AT B
                         (the hidden terminal problem), even if they cannot
                         hear each other.

    For rule 2 we look at each node B and connect all of B's neighbours to
    each other, because any two of them would both reach B.
    """
    conflict = nx.Graph()
    conflict.add_nodes_from(radio.nodes)

    for b in radio.nodes:
        neighbours = list(radio.neighbors(b))

        for a in neighbours:                      # rule 1
            conflict.add_edge(b, a)

        for i, a in enumerate(neighbours):        # rule 2
            for c in neighbours[i + 1:]:
                conflict.add_edge(a, c)

    return conflict
