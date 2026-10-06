#!/usr/bin/env python3
"""TDMA Schedule Planner: the command line entry point.

Examples:
  python3 schedule.py '{"Node_01":[0,0],"Node_02":[300,0], ...}'
  python3 schedule.py --file examples/grid_4x4.json --plot output/grid.png
"""

import argparse
import sys

from tdma.planner import make_plan
from tdma.report import render, to_json
from tdma.topology import parse_nodes


def main():
    p = argparse.ArgumentParser(description="Conflict-free TDMA slot planner "
                                            "(distance-2 graph colouring).")
    p.add_argument("nodes_json", nargs="?",
                   help='node coordinates, e.g. \'{"Node_01":[0,0],...}\'')
    p.add_argument("--file", help="read the node JSON from a file instead")
    p.add_argument("--range", type=float, default=500.0,
                   help="radio range in metres (default 500)")
    p.add_argument("--rounds", type=int, default=300,
                   help="iterated greedy rounds (default 300)")
    p.add_argument("--seed", type=int, default=0, help="random seed")
    p.add_argument("--exact-seconds", type=float, default=5.0,
                   help="time limit for the exact search (default 5)")
    p.add_argument("--json-out", help="also save the schedule as JSON (for Part 2)")
    p.add_argument("--plot", help="also save a picture of the network (PNG)")
    args = p.parse_args()

    if args.file:
        with open(args.file) as f:
            text = f.read()
    elif args.nodes_json:
        text = args.nodes_json
    else:
        p.error("give node JSON as an argument or with --file")

    try:
        nodes = parse_nodes(text)
    except ValueError as e:        # json errors are ValueErrors too
        p.error(f"bad node input: {e}")

    plan = make_plan(nodes, radio_range=args.range, rounds=args.rounds,
                     seed=args.seed, exact_seconds=args.exact_seconds)

    print(render(plan))

    if args.json_out:
        with open(args.json_out, "w") as f:
            f.write(to_json(plan))
    if args.plot:
        from tdma.plot import draw
        draw(plan, args.plot)

    return 1 if plan.problems else 0


if __name__ == "__main__":
    sys.exit(main())
