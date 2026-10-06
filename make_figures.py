#!/usr/bin/env python3
"""Regenerate every figure used in the report and slides (writes to output/)."""

import json
import sys

sys.path.insert(0, "emane")

from bridge import naive_one_hop_schedule  # noqa: E402
from tdma.analysis import verify  # noqa: E402
from tdma.planner import make_plan  # noqa: E402
from tdma.plot import draw, draw_comparison  # noqa: E402
from tdma.report import render, to_json  # noqa: E402
from tdma.topology import parse_nodes  # noqa: E402

for name in ["grid_4x4", "convoy_line", "two_clusters", "random_field"]:
    plan = make_plan(parse_nodes(open(f"examples/{name}.json").read()))
    draw(plan, f"output/{name}.png")
    with open(f"output/{name}_report.txt", "w") as f:
        f.write(render(plan) + "\n")
    if name == "grid_4x4":
        with open("output/schedule.json", "w") as f:
            f.write(to_json(plan))
        naive = naive_one_hop_schedule(json.loads(to_json(plan)))
        draw_comparison(plan.nodes, plan.radio, naive, plan.slots,
                        verify(plan.radio, naive), "output/naive_vs_ours.png")
print("figures and reports written to output/")
