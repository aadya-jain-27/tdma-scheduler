#!/usr/bin/env python3
"""Stress test: how close does each method get to the theoretical minimum?

For each network size we generate many random layouts (same average radio
density as a 16-node, 1.5 km field), run every method, and measure the
"gap" = slots used minus the lower bound. Gap 0 means proven optimal.

  python3 benchmark.py            # writes output/benchmark.png and .md
"""

import math
import random
import time

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from tdma.analysis import lower_bound, verify  # noqa: E402
from tdma.coloring import (HEURISTICS, exact_improve, iterated_greedy,  # noqa: E402
                           slot_count)
from tdma.topology import build_conflict_graph, build_radio_graph  # noqa: E402

SIZES = [16, 32, 64, 100, 150]
LAYOUTS = 40
METHODS = list(HEURISTICS) + ["+ Iterated Greedy", "+ Exact Search (final)"]
COLOURS = ["#2a78d6", "#eb6834", "#1baf7a", "#4a3aa7", "#e34948"]


def random_layout(n, seed):
    # Keep the density of the 16 node / 1500 m example: about 140,000 m^2 per radio.
    side = math.sqrt(n * 1500 ** 2 / 16)
    r = random.Random(seed)
    return {f"N{i:03d}": (r.uniform(0, side), r.uniform(0, side)) for i in range(n)}


def run():
    rows = []
    for n in SIZES:
        gaps = {m: 0 for m in METHODS}
        optimal = proven = 0
        seconds = 0.0
        for seed in range(LAYOUTS):
            radio = build_radio_graph(random_layout(n, seed), 500)
            conflict = build_conflict_graph(radio)
            _, bound = lower_bound(radio, conflict)

            t = time.perf_counter()
            results = {name: fn(conflict) for name, fn in HEURISTICS.items()}
            best = min(results.values(), key=slot_count)
            improved = iterated_greedy(conflict, best, rounds=300, seed=seed)
            final, is_proven = exact_improve(conflict, improved, bound, 2.0)
            seconds += time.perf_counter() - t

            assert verify(radio, final) == []
            for name, s in results.items():
                gaps[name] += slot_count(s) - bound
            gaps["+ Iterated Greedy"] += slot_count(improved) - bound
            gaps["+ Exact Search (final)"] += slot_count(final) - bound
            optimal += slot_count(final) == bound
            proven += is_proven

        rows.append({
            "n": n,
            "gaps": {m: g / LAYOUTS for m, g in gaps.items()},
            "hit_bound": 100 * optimal / LAYOUTS,
            "proven": 100 * proven / LAYOUTS,
            "ms": 1000 * seconds / LAYOUTS,
        })
        print(f"n={n:>3}  " + "  ".join(f"{m.split()[0]}={g / LAYOUTS:.2f}"
                                        for m, g in gaps.items())
              + f"  proven={100 * proven / LAYOUTS:.0f}%")
    return rows


def chart(rows, path):
    fig, ax = plt.subplots(figsize=(8, 4.6))
    xs = [r["n"] for r in rows]
    # Three methods are 0 at every size; draw them as one line so none hides.
    series = [
        ("Largest-First Greedy", [r["gaps"]["Largest-First Greedy"] for r in rows], "#2a78d6"),
        ("DSATUR", [r["gaps"]["DSATUR"] for r in rows], "#eb6834"),
        ("Smallest-Last, + Iterated Greedy, final pipeline",
         [max(r["gaps"][m] for m in METHODS[1:2] + METHODS[3:]) for r in rows], "#1baf7a"),
    ]
    for label, ys, colour in series:
        ax.plot(xs, ys, color=colour, linewidth=2, marker="o", markersize=6,
                markeredgecolor="white", markeredgewidth=1.5, label=label, clip_on=False)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color("#bbbbbb")
    ax.grid(axis="y", color="#e6e6e6", linewidth=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(colors="#52514e")
    ax.set_xticks(xs)
    ax.set_ylim(0, max(0.3, max(max(s[1]) for s in series) * 1.2))
    ax.set_xlabel("Number of radios in the network", color="#52514e")
    ax.set_ylabel("Extra slots above the proven minimum\n(average, lower is better)",
                  color="#52514e")
    ax.set_title(f"How close each method gets to the minimum ({LAYOUTS} random layouts per size)",
                 color="#0b0b0b", loc="left", fontsize=11)
    ax.legend(frameon=False, fontsize=9, loc="upper left")
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def table(rows, path):
    head = "| Radios | " + " | ".join(METHODS) + " | Final hits bound | Proven optimal | Avg time |"
    lines = [head, "|" + "---|" * (len(METHODS) + 4)]
    for r in rows:
        lines.append(f"| {r['n']} | " + " | ".join(f"{r['gaps'][m]:.2f}" for m in METHODS)
                     + f" | {r['hit_bound']:.0f}% | {r['proven']:.0f}% | {r['ms']:.0f} ms |")
    with open(path, "w") as f:
        f.write("Average extra slots above the lower bound (0 = optimal)\n\n")
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    rows = run()
    chart(rows, "output/benchmark.png")
    table(rows, "output/benchmark.md")
    print("saved output/benchmark.png and output/benchmark.md")
