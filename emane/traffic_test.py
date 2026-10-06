#!/usr/bin/env python3
"""Runs INSIDE the EMANE container. Every radio pings every 1-hop neighbour
at the same time (so the channel is busy, like a real network), then we
report the packet loss per link.

With our distance-2 schedule, loss should be near 0%.
With the naive distance-1 schedule, links that suffer a hidden terminal
should lose packets, because two senders hit the same receiver in one slot.
"""

import json
import math
import re
import subprocess
import sys

data = json.load(open(sys.argv[1]))
label = sys.argv[2]
names, pos, rng = data["nodes"], data["positions"], data["radio_range_m"]

jobs = []
for i, a in enumerate(names, 1):
    for j, b in enumerate(names, 1):
        if i != j and math.dist(pos[a], pos[b]) <= rng:
            cmd = ["ip", "netns", "exec", f"n{i}", "ping", "-q", "-c", "50",
                   "-i", "0.05", "-W", "1", f"10.100.0.{j}"]
            jobs.append((a, b, subprocess.Popen(cmd, stdout=subprocess.PIPE, text=True)))

lines, total = [], 0.0
for a, b, proc in jobs:
    out = proc.communicate()[0]
    m = re.search(r"([\d.]+)% packet loss", out)
    loss = float(m.group(1)) if m else 100.0
    total += loss
    lines.append(f"{a} -> {b}: {loss:5.1f}% loss")

summary = f"[{label}] {len(jobs)} links tested, average loss {total / len(jobs):.1f}%"
with open(f"output/emane_results_{label}.txt", "w") as f:
    f.write(summary + "\n" + "\n".join(lines) + "\n")
print(summary)
