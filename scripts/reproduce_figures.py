#!/usr/bin/env python3
"""Regenerate public-safe figures from the deidentified release tables."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/deidentified"
OUTPUT = ROOT / "figures/reproduced"

COLORS = {
    "history": "#009E73",
    "vigilance": "#0072B2",
    "asm": "#E69F00",
    "both": "#CC79A7",
    "neither": "#999999",
}


def configure_style() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 9,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.linewidth": 0.8,
            "savefig.dpi": 240,
            "savefig.bbox": "tight",
        }
    )
    OUTPUT.mkdir(parents=True, exist_ok=True)


def detectability_classes(detectability: pd.DataFrame) -> pd.Series:
    def excludes_zero(prefix: str) -> pd.Series:
        lower = detectability[f"{prefix}_lo95_B2000"]
        upper = detectability[f"{prefix}_hi95_B2000"]
        return (lower > 0) | (upper < 0)

    vigilance = excludes_zero("sa_V")
    asm = excludes_zero("sa_A")
    label = pd.Series("neither", index=detectability.index)
    label[vigilance & ~asm] = "vigilance"
    label[~vigilance & asm] = "asm"
    label[vigilance & asm] = "both"
    return label


def figure2() -> Path:
    dependency = pd.read_csv(DATA / "ppglm/dependency_coordinates.csv")
    detectability = pd.read_csv(DATA / "ppglm/bootstrap_detectability.csv")
    detectability = detectability.set_index("participant_id").loc[
        dependency["participant_id"]
    ]
    classes = detectability_classes(detectability).to_numpy()

    columns = ["sa_H_ev", "sa_V_ev", "sa_A_ev"]
    coordinates = dependency[columns].to_numpy(float)
    shared_scale = np.median(np.abs(coordinates[np.isfinite(coordinates)]))
    clip = np.quantile(np.abs(coordinates[np.isfinite(coordinates)]), 0.98)
    transformed = np.arcsinh(
        coordinates
        / np.array(
            [np.median(np.abs(coordinates[:, index])) for index in range(3)]
        )
    )
    order = np.argsort(-coordinates[:, 0])

    fig = plt.figure(figsize=(11.0, 7.0))
    grid = fig.add_gridspec(
        2, 3, height_ratios=[0.72, 1.0], hspace=0.42, wspace=0.35
    )
    heat = fig.add_subplot(grid[0, :])
    rendered = np.arcsinh(
        np.clip(coordinates[order], -clip, clip) / shared_scale
    ).T
    image = heat.imshow(
        rendered, aspect="auto", cmap="RdBu_r", interpolation="none"
    )
    heat.set_yticks(range(3), ["History", "Vigilance", "ASM"])
    heat.set_xticks([])
    heat.set_xlabel("114 participants, ordered by history coordinate")
    heat.set_title(
        "A  Signed held-out deviance improvement per IED-positive second",
        loc="left",
        weight="bold",
    )
    colorbar = fig.colorbar(image, ax=heat, fraction=0.018, pad=0.018)
    colorbar.set_label("asinh-scaled coordinate")

    pairs = [(0, 1), (0, 2), (1, 2)]
    names = ["History", "Vigilance", "ASM"]
    panel_names = ["B", "C", "D"]
    projection_axes = []
    for column, ((x_index, y_index), panel) in enumerate(zip(pairs, panel_names)):
        axis = fig.add_subplot(grid[1, column])
        projection_axes.append(axis)
        for group in ("neither", "vigilance", "asm", "both"):
            keep = classes == group
            axis.scatter(
                transformed[keep, x_index],
                transformed[keep, y_index],
                s=25,
                color=COLORS[group] if group != "neither" else "white",
                edgecolor=COLORS[group],
                linewidth=0.9,
                alpha=0.88,
                label={
                    "both": "Vigilance & ASM",
                    "vigilance": "Vigilance only",
                    "asm": "ASM only",
                    "neither": "Vigilance & ASM ≈ 0",
                }[group],
            )
        axis.axhline(0, color="#DDDDDD", linewidth=0.7)
        axis.axvline(0, color="#DDDDDD", linewidth=0.7)
        axis.set_xlabel(names[x_index])
        axis.set_ylabel(names[y_index])
        axis.set_title(panel, loc="left", weight="bold")
    projection_axes[-1].legend(frameon=False, fontsize=7, loc="best")
    fig.suptitle(
        "Dependency structure of IED timing", fontsize=14, weight="bold", y=1.01
    )
    target = OUTPUT / "figure2_dependency_structure.png"
    fig.savefig(target)
    plt.close(fig)
    return target


def figure3() -> Path:
    curves = pd.read_csv(DATA / "history/history_curves.csv.gz")
    labels = pd.to_numeric(curves["figure3_example"], errors="coerce")
    curves = curves[labels.notna()].copy()
    curves["figure3_example"] = labels[labels.notna()].astype(int)
    summary = json.loads((DATA / "history/figure3_examples.json").read_text())
    by_label = {index + 1: value for index, value in enumerate(summary)}

    fig, axes = plt.subplots(3, 2, figsize=(10.0, 8.2), sharex=True)
    for label, axis in enumerate(axes.flat, 1):
        frame = curves[curves["figure3_example"] == label]
        axis.fill_between(
            frame["lag_s"].to_numpy(),
            frame["lower_95"].to_numpy(),
            frame["upper_95"].to_numpy(),
            color="#D1D3D4",
        )
        axis.plot(
            frame["lag_s"], frame["full_multiplier"], color="black", linewidth=1.4
        )
        axis.axhline(1, color="#555555", linestyle="--", linewidth=0.8)
        metric = by_label[label]
        axis.set_title(f"Participant {label}", weight="bold")
        axis.text(
            0.98,
            0.94,
            f"rate {metric['merged_onset_responses_per_min']:.2f}/min\n"
            f"peak {metric['peak_multiplier']:.2f}×",
            transform=axis.transAxes,
            ha="right",
            va="top",
            fontsize=8,
            color="#444444",
        )
        axis.set_xlim(0, 90)
        axis.set_ylim(bottom=0)
        axis.set_ylabel("Rate multiplier")
        axis.set_xlabel("Lag (s)")
    fig.suptitle(
        "Rate-matched participants have distinct history curves",
        fontsize=14,
        weight="bold",
    )
    fig.tight_layout()
    target = OUTPUT / "figure3_rate_matched_histories_public.png"
    fig.savefig(target)
    plt.close(fig)
    return target


def figure4() -> Path:
    curves = pd.read_csv(DATA / "history/repeat_recording_curves.csv.gz")
    summary = json.loads((DATA / "history/figure4_summary.json").read_text())
    roc = pd.read_csv(DATA / "history/figure4_roc_curves.csv")

    fig = plt.figure(figsize=(10.5, 8.2))
    grid = fig.add_gridspec(
        3, 2, height_ratios=[1, 1, 1.15], hspace=0.42, wspace=0.28
    )
    for position, participant in enumerate(summary["selected"]):
        axis = fig.add_subplot(grid[position // 2, position % 2])
        frame = curves[curves["participant_id"] == participant["participant_id"]]
        for recording, color in (("A", "#333333"), ("B", "#0072B2")):
            record = frame[frame["recording"] == recording]
            axis.fill_between(
                record["lag_s"].to_numpy(),
                record["lower_95"].to_numpy(),
                record["upper_95"].to_numpy(),
                color=color,
                alpha=0.10,
                linewidth=0,
            )
            axis.plot(
                record["lag_s"],
                record["multiplier"],
                color=color,
                linewidth=1.3,
                label=f"Recording {recording}",
            )
        axis.axhline(1, color="#777777", linestyle="--", linewidth=0.7)
        axis.set_title(f"Participant {participant['panel']}", weight="bold")
        axis.set_xlabel("Lag (s)")
        axis.set_ylabel("Rate multiplier")
        axis.set_xlim(0, 90)
        axis.set_ylim(bottom=0)
        if position == 0:
            axis.legend(frameon=False, fontsize=8)

    axis = fig.add_subplot(grid[2, :])
    for comparison, color, label in (
        (
            "same_recording_split_halves",
            "#3953A4",
            "Same recording, two halves",
        ),
        (
            "same_participant_repeat_recording",
            "#555555",
            "Same participant, repeat recording",
        ),
    ):
        frame = roc[roc["comparison"] == comparison]
        auc = frame["auc"].iloc[0]
        axis.plot(
            frame["false_positive_rate"],
            frame["true_positive_rate"],
            color=color,
            linewidth=1.8,
            label=f"{label} · AUC {auc:.2f}",
        )
    axis.plot([0, 1], [0, 1], color="#999999", linestyle="--", linewidth=0.8)
    axis.set(
        xlim=(0, 1),
        ylim=(0, 1),
        xlabel="False-positive rate",
        ylabel="True-positive rate",
    )
    axis.legend(frameon=False, loc="lower right")
    axis.set_title("Discriminability from history-curve similarity", weight="bold")
    fig.suptitle(
        "Reproducibility of participant-specific history curves",
        fontsize=14,
        weight="bold",
    )
    target = OUTPUT / "figure4_reproducibility.png"
    fig.savefig(target)
    plt.close(fig)
    return target


def figure6() -> Path:
    data = pd.read_csv(DATA / "sleep_state_densities.csv")
    summary = json.loads((DATA / "sleep_density_ae114.json").read_text())
    stages = ["wake", "n1", "n2", "n3", "rem"]
    labels = ["Wake", "N1", "N2", "N3", "REM"]
    values = []
    for stage in stages:
        keep = (data[f"{stage}_seconds"] >= 1800) & (
            data[f"{stage}_ied_positive_seconds"] > 0
        )
        if stage != "wake":
            keep &= (data["wake_seconds"] >= 1800) & (
                data["wake_ied_positive_seconds"] > 0
            )
        values.append(data.loc[keep, f"{stage}_density_per_min"].to_numpy(float))

    fig, axis = plt.subplots(figsize=(7.4, 5.5))
    rng = np.random.default_rng(1)
    for index, value in enumerate(values, 1):
        axis.scatter(
            index + rng.uniform(-0.11, 0.11, len(value)),
            value,
            s=11,
            color="#BDBDBD",
            alpha=0.45,
            edgecolor="none",
        )
    axis.boxplot(
        values,
        widths=0.34,
        showfliers=False,
        boxprops={"color": "#3953A4", "linewidth": 1.2},
        medianprops={"color": "#ED2024", "linewidth": 1.4},
        whiskerprops={"color": "#333333", "linestyle": "--"},
        capprops={"color": "#333333"},
    )
    axis.set_yscale("log")
    axis.set_xticks(range(1, 6), labels)
    axis.set_ylabel("IED-positive-second density (min⁻¹)")
    axis.set_xlabel("Vigilance state")
    axis.set_title(
        "Sleep-stage modulation of IED density", fontsize=14, weight="bold"
    )
    for index, stage in enumerate(stages[1:], 2):
        gm = summary[stage]["geomean_ratio"]
        axis.text(
            index + 0.22,
            np.exp(np.mean(np.log(values[index - 1]))),
            f"{gm:.1f}×",
            weight="bold",
            va="center",
        )
    target = OUTPUT / "figure6_sleep_density.png"
    fig.savefig(target)
    plt.close(fig)
    return target


def main() -> int:
    configure_style()
    outputs = [figure2(), figure3(), figure4(), figure6()]
    for output in outputs:
        rendered = plt.imread(output)
        if (
            rendered.ndim not in (2, 3)
            or min(rendered.shape[:2]) < 500
            or float(np.nanmax(rendered) - np.nanmin(rendered)) < 0.2
        ):
            raise RuntimeError(f"invalid or blank rendered figure: {output}")
        print(output.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
