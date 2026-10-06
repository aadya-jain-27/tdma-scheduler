#!/usr/bin/env python3
"""Summarise the EMANE runs: packet loss per run and why packets were dropped.

Reads the files written by run_demo.sh in output/ and writes
output/emane_summary.md and output/emane_results.png.

  python3 emane/summarize.py
"""

import glob
import re

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

RUNS = [("1 ms slots", ""), ("5 ms slots", "_5ms")]
DROP_TABLES = ["UnicastByteDropTable0", "BroadcastByteDropTable0"]


def average_loss(label):
    with open(f"output/emane_results_{label}.txt") as f:
        return float(re.search(r"average loss ([\d.]+)%", f.readline()).group(1))


def links_without_loss(label):
    with open(f"output/emane_results_{label}.txt") as f:
        return sum(1 for line in f if line.rstrip().endswith(" 0.0% loss"))


def drop_reasons(label):
    """Add up the dropped bytes per reason over all NEMs.
    'Dst MAC' is left out: it only means the packet was for someone else."""
    totals = {}
    for path in glob.glob(f"output/emane_raw/{label}_drops_nem*.txt"):
        text = open(path).read()
        for table in DROP_TABLES:
            m = re.search(table + r"\n(\|.*\|)\n((?:\|.*\|\n)*)", text)
            if not m:
                continue
            header = [h.strip() for h in m.group(1).strip("|").split("|")]
            for row in m.group(2).strip().splitlines():
                values = [v.strip() for v in row.strip("|").split("|")]
                for name, value in zip(header[1:], values[1:]):
                    if value.isdigit() and name != "Dst MAC":
                        totals[name] = totals.get(name, 0) + int(value)
    return totals


def main():
    lines = ["| Run | Schedule | Average loss | Links with 0% loss | Collision drops (SINR, bytes) | Timing drops (Slot Error + Long, bytes) |",
             "|---|---|---|---|---|---|"]
    bars = []
    for run_name, suffix in RUNS:
        for sched, label in [("distance-2 (ours)", "optimized"), ("one-hop (naive)", "naive")]:
            label += suffix
            loss = average_loss(label)
            drops = drop_reasons(label)
            timing = drops.get("Slot Error", 0) + drops.get("Long", 0)
            lines.append(f"| {run_name} | {sched} | {loss:.1f}% | {links_without_loss(label)} / 84 "
                         f"| {drops.get('SINR', 0)} | {timing} |")
            bars.append((run_name, sched, loss))

    with open("output/emane_summary.md", "w") as f:
        f.write("EMANE results, 4x4 grid, 84 one-hop links, 50 pings per link\n\n")
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))

    fig, ax = plt.subplots(figsize=(7, 4))
    width = 0.36
    for k, (sched, colour) in enumerate([("distance-2 (ours)", "#2a78d6"), ("one-hop (naive)", "#eb6834")]):
        ys = [b[2] for b in bars if b[1] == sched]
        xs = [i + (k - 0.5) * width for i in range(len(RUNS))]
        ax.bar(xs, ys, width * 0.92, color=colour, label=sched)
        for x, y in zip(xs, ys):
            ax.text(x, y + 1.5, f"{y:.1f}%", ha="center", fontsize=9, color="#333333")
    ax.set_xticks(range(len(RUNS)))
    ax.set_xticklabels([r[0] for r in RUNS])
    ax.set_ylabel("Average packet loss (%)")
    ax.set_ylim(0, 100)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.grid(axis="y", color="#e6e6e6")
    ax.set_axisbelow(True)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig("output/emane_results.png", dpi=160)
    plt.close(fig)


if __name__ == "__main__":
    main()
