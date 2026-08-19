#!/usr/bin/env python3
"""Render Figure S3 with terminology aligned to the authoritative manuscript."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


HERE = Path(__file__).resolve().parent
TABLES = HERE / "tables"
OUTPUT = HERE.parent / "figures" / "figure_s3_kernel_correlations_reproduced"

correlations = pd.read_csv(
    TABLES / "table_sb_kernel_feature_correlations.csv", index_col=0
).to_numpy(dtype=float)
q_values = pd.read_csv(
    TABLES / "table_sb_kernel_feature_qvalues.csv", index_col=0
).to_numpy(dtype=float)

labels = [
    "Age",
    "Log modeled onset-response rate\n(post-first-onset hours)",
    "Apparent refractory\ninterval",
    "Peak lag",
    "Peak\nmultiplier",
    "40–70 s\nmultiplier",
    "Split-half residual\ncorrelation",
]

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9})
fig, ax = plt.subplots(figsize=(8.6, 6.8))
fig.subplots_adjust(left=0.36, right=0.88, bottom=0.30, top=0.90)
image = ax.imshow(correlations, cmap="RdBu_r", vmin=-1, vmax=1)

ax.set_title("Kernel features and cohort characteristics", fontsize=14, weight="bold", pad=10)
ax.set_xticks(np.arange(len(labels)), labels=labels, rotation=48, ha="right", rotation_mode="anchor")
ax.set_yticks(np.arange(len(labels)), labels=labels)
ax.tick_params(length=0)

for edge in np.arange(-0.5, len(labels), 1):
    ax.axhline(edge, color="white", linewidth=0.7)
    ax.axvline(edge, color="white", linewidth=0.7)

for row in range(correlations.shape[0]):
    for column in range(correlations.shape[1]):
        value = correlations[row, column]
        marker = "*" if row != column and q_values[row, column] < 0.05 else ""
        color = "white" if abs(value) >= 0.5 else "#222222"
        ax.text(column, row, f"{value:.2f}{marker}", ha="center", va="center", color=color, fontsize=9)

colorbar = fig.colorbar(image, ax=ax, fraction=0.045, pad=0.035)
colorbar.set_label(r"Spearman $\rho$", fontsize=11)
colorbar.set_ticks([-1, -0.5, 0, 0.5, 1])

for spine in ax.spines.values():
    spine.set_visible(False)

fig.savefig(OUTPUT.with_suffix(".png"), dpi=300, facecolor="white")
fig.savefig(OUTPUT.with_suffix(".svg"), facecolor="white")
fig.savefig(OUTPUT.with_suffix(".pdf"), facecolor="white")
