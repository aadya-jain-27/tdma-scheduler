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


def draw_comparison(nodes, radio, naive, ours, problems, path):
    """Side by side: a naive distance-1 schedule (with its collisions in red)
    next to our distance-2 schedule."""
    fig, axes = plt.subplots(1, 2, figsize=(12, 6.8))
    pairs = [(p.split()[0], p.split()[2]) for p in problems]
    panels = [(axes[0], naive, pairs,
               f"Naive (distance-1 only): {slot_count(naive)} slots, "
               f"{len(pairs)} hidden-terminal collisions"),
              (axes[1], ours, [],
               f"Ours (distance-2): {slot_count(ours)} slots, 0 collisions")]
    for ax, slots, bad, title in panels:
        palette = plt.get_cmap("tab10")
        for a, b in radio.edges:
            (x1, y1), (x2, y2) = nodes[a], nodes[b]
            ax.plot([x1, x2], [y1, y2], color="#cccccc", linewidth=0.8, zorder=1)
        for a, b in bad:
            (x1, y1), (x2, y2) = nodes[a], nodes[b]
            ax.plot([x1, x2], [y1, y2], color="#e34948", linewidth=1.6,
                    linestyle="--", zorder=1.5)
        for name, (x, y) in nodes.items():
            ax.scatter(x, y, s=600, color=palette(slots[name] % 10),
                       edgecolor="black", zorder=2)
            ax.text(x, y, f"{column_label(name)}\nS{slots[name]}", ha="center",
                    va="center", fontsize=8, fontweight="bold", zorder=3)
        ax.set_title(title, fontsize=11, pad=18)
        ax.set_aspect("equal")
        ax.margins(0.12)
        ax.set_xticks([])
        ax.set_yticks([])
        for side in ax.spines.values():
            side.set_visible(False)
    fig.text(0.25, 0.04, "red dashed line = two radios in the same slot that both reach "
             "a shared neighbour", ha="center", fontsize=9, color="#e34948")
    fig.tight_layout(rect=(0, 0.06, 1, 0.97))
    fig.savefig(path, dpi=150)
    plt.close(fig)
