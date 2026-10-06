"""Draw the network: radios coloured by slot, links, and range circles."""

import matplotlib

matplotlib.use("Agg")              # draw to a file, no window needed
import matplotlib.pyplot as plt    # noqa: E402

from .coloring import slot_count   # noqa: E402
from .report import column_label   # noqa: E402


def draw(plan, path):
    frame = slot_count(plan.slots)
    palette = plt.get_cmap("tab20" if frame > 10 else "tab10")
    fig, ax = plt.subplots(figsize=(8, 8))

    # Faint circles show each radio's 500 m reach.
    for name, (x, y) in plan.nodes.items():
        ax.add_patch(plt.Circle((x, y), plan.radio_range,
                                color=palette(plan.slots[name] % 20),
                                alpha=0.04, linewidth=0))

    # Grey lines are radio links (pairs that can hear each other).
    for a, b in plan.radio.edges:
        (x1, y1), (x2, y2) = plan.nodes[a], plan.nodes[b]
        ax.plot([x1, x2], [y1, y2], color="#999999", linewidth=0.8, zorder=1)

    # Dots: colour = time slot. Same colour = transmitting at the same time.
    for name, (x, y) in plan.nodes.items():
        s = plan.slots[name]
        ax.scatter(x, y, s=650, color=palette(s % 20), edgecolor="black", zorder=2)
        ax.text(x, y, f"{column_label(name)}\nS{s}", ha="center", va="center",
                fontsize=8, fontweight="bold", zorder=3)

    ax.set_title(f"TDMA schedule: {len(plan.nodes)} radios, {frame} slots "
                 f"(minimum possible: {plan.lower_bound})")
    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")
    ax.set_aspect("equal")
    ax.margins(0.15)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
