"""
Renders docs/bridge.png (waterfall of the reconciliation bridge) and
docs/breakdown.png (per-root campaign view). Numbers come from the SQL files,
not from constants, so the chart can never disagree with the bridge.

    pip install matplotlib   # only dependency, only for this script
    python make_charts.py
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
SQL = ROOT / "sql"
DOCS = ROOT / "docs"
DOCS.mkdir(exist_ok=True)

# Palette: neutral for totals, one accent for removals, muted ink for text.
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e6e5e1"
TOTAL, REMOVE, KEEP = "#2a78d6", "#eb6834", "#1baf7a"
SURFACE = "#fcfcfb"

con = sqlite3.connect(ROOT / "data" / "comm_log.db")


def scalar(rel: str) -> int:
    (v,) = con.execute((SQL / rel).read_text()).fetchone()
    return int(v)


# ------------------------------------------------------------- bridge chart --
steps = [
    ("Naive\nrow count", scalar("bridge/00_naive.sql")),
    ("Scope filters\n(no-op)", scalar("bridge/01_scope.sql")),
    ("Drop unapproved\ncampaign 9004", scalar("bridge/02_eligible_campaigns.sql")),
    ("Collapse retry\nchain 9001", scalar("bridge/03_collapse_family_a.sql")),
    ("Collapse retry\nchain 9201", scalar("bridge/04_final.sql")),
]

fig, ax = plt.subplots(figsize=(9, 4.6), dpi=160)
fig.patch.set_facecolor(SURFACE)
ax.set_facecolor(SURFACE)

x = 0
prev = None
for i, (label, val) in enumerate(steps):
    if prev is None:
        ax.bar(x, val, width=0.6, color=TOTAL, edgecolor=SURFACE, linewidth=2)
        ax.text(x, val + 0.6, str(val), ha="center", va="bottom", color=INK, fontsize=11, fontweight="bold")
    else:
        delta = val - prev
        if delta == 0:
            ax.bar(x, 0.15, bottom=prev - 0.075, width=0.6, color=GRID)
            ax.text(x, prev + 0.6, "±0", ha="center", va="bottom", color=INK2, fontsize=10)
        else:
            ax.bar(x, delta, bottom=prev, width=0.6, color=REMOVE, edgecolor=SURFACE, linewidth=2)
            ax.text(x, prev + 0.6, f"{delta:+d}", ha="center", va="bottom", color=INK, fontsize=11, fontweight="bold")
        ax.plot([x - 1 + 0.3, x - 0.3], [prev, prev], color=INK2, linewidth=1, linestyle=(0, (2, 2)))
    prev = val
    x += 1

# final total bar
ax.plot([x - 1 + 0.3, x - 0.3], [prev, prev], color=INK2, linewidth=1, linestyle=(0, (2, 2)))
ax.bar(x, prev, width=0.6, color=TOTAL, edgecolor=SURFACE, linewidth=2)
ax.text(x, prev + 0.6, f"{prev}", ha="center", va="bottom", color=INK, fontsize=11, fontweight="bold")

labels = [s[0] for s in steps] + ["Final\ntarget_base"]
ax.set_xticks(range(len(labels)))
ax.set_xticklabels(labels, color=INK2, fontsize=9)
ax.set_ylim(0, 34)
ax.set_yticks([0, 10, 20, 30])
ax.tick_params(axis="y", colors=INK2, labelsize=9, length=0)
ax.tick_params(axis="x", length=0)
ax.yaxis.grid(True, color=GRID, linewidth=1)
ax.set_axisbelow(True)
for s in ("top", "right", "left"):
    ax.spines[s].set_visible(False)
ax.spines["bottom"].set_color(GRID)
ax.set_title("Reconciliation bridge: 30 raw rows to Finance's 22  (merchant 501, Oct-2026)",
             loc="left", color=INK, fontsize=11, pad=12)
fig.tight_layout()
fig.savefig(DOCS / "bridge.png", facecolor=SURFACE)
plt.close(fig)

# ---------------------------------------------------------- breakdown chart --
rows = con.execute((SQL / "bridge" / "04_final_breakdown.sql").read_text()).fetchall()
# root_id, name, has_retries, raw_rows, distinct_customers, qualifying
names = [f"{r[1]}\n({'retry family' if r[2] else 'standalone'})" for r in rows]
raw = [r[3] for r in rows]
qual = [r[5] for r in rows]

fig, ax = plt.subplots(figsize=(9, 3.6), dpi=160)
fig.patch.set_facecolor(SURFACE)
ax.set_facecolor(SURFACE)
y = range(len(rows))
ax.barh([i + 0.2 for i in y], raw, height=0.36, color=GRID, label="raw log rows")
ax.barh([i - 0.2 for i in y], qual, height=0.36, color=KEEP, label="qualifying sends (target_base)")
for i, (r, q) in enumerate(zip(raw, qual)):
    ax.text(r + 0.25, i + 0.2, str(r), va="center", color=INK2, fontsize=9)
    ax.text(q + 0.25, i - 0.2, str(q), va="center", color=INK, fontsize=10, fontweight="bold")
ax.set_yticks(list(y))
ax.set_yticklabels(names, color=INK2, fontsize=9)
ax.invert_yaxis()
ax.set_xlim(0, 15)
ax.set_xticks([0, 5, 10, 15])
ax.tick_params(colors=INK2, labelsize=9, length=0)
ax.xaxis.grid(True, color=GRID, linewidth=1)
ax.set_axisbelow(True)
for s in ("top", "right", "left"):
    ax.spines[s].set_visible(False)
ax.spines["bottom"].set_color(GRID)
ax.legend(loc="lower right", frameon=False, fontsize=9, labelcolor=INK2)
ax.set_title(f"Where the 22 comes from: {' + '.join(map(str, qual))} = {sum(qual)}",
             loc="left", color=INK, fontsize=11, pad=12)
fig.tight_layout()
fig.savefig(DOCS / "breakdown.png", facecolor=SURFACE)
print("wrote docs/bridge.png and docs/breakdown.png")
