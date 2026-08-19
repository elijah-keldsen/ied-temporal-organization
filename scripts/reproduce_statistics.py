#!/usr/bin/env python3
"""Recompute the numerical claims shared by the manuscript and appendix."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/deidentified"


@dataclass(frozen=True)
class Claim:
    section: str
    statistic: str
    reported: str
    reproduced: str

    @property
    def matches(self) -> bool:
        return self.reported == self.reproduced


def load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def short_kernel_separation() -> tuple[np.ndarray, np.ndarray, float]:
    curves = pd.read_csv(
        DATA / "history/manuscript_short_history_curves.csv.gz"
    )
    participant_ids = sorted(curves["participant_id"].unique())

    def matrix(column: str) -> np.ndarray:
        return np.stack(
            [
                np.log(
                    curves.loc[curves.participant_id == participant_id, column]
                    .to_numpy(float)
                )
                for participant_id in participant_ids
            ]
        )

    full = matrix("full_multiplier")
    half_a = matrix("split_a_multiplier")
    half_b = matrix("split_b_multiplier")
    cohort_template = full.mean(axis=0)
    within = np.array(
        [
            np.corrcoef(
                half_a[index] - cohort_template,
                half_b[index] - cohort_template,
            )[0, 1]
            for index in range(len(participant_ids))
        ]
    )
    between = []
    for left in range(len(participant_ids)):
        for right in range(left + 1, len(participant_ids)):
            between.extend(
                [
                    np.corrcoef(
                        half_a[left] - cohort_template,
                        half_b[right] - cohort_template,
                    )[0, 1],
                    np.corrcoef(
                        half_b[left] - cohort_template,
                        half_a[right] - cohort_template,
                    )[0, 1],
                ]
            )
    between_array = np.asarray(between)
    auc = mannwhitneyu(within, between_array, alternative="greater").statistic / (
        within.size * between_array.size
    )
    return within, between_array, float(auc)


def claims() -> list[Claim]:
    cohort = pd.read_csv(DATA / "cohort_features.csv")
    dependency = pd.read_csv(DATA / "ppglm/dependency_coordinates.csv")
    population = load_json(DATA / "ppglm/population_inference.json")
    detectability = load_json(DATA / "ppglm/detectability_summary.json")
    figure4 = load_json(DATA / "history/figure4_summary.json")
    sleep = load_json(DATA / "sleep_density_ae114.json")
    sleep_pairs = load_json(DATA / "sleep_density_pairwise_ae114.json")["pairs"]

    fine_hours = cohort["fine_kernel_post_first_onset_hours"]
    ppglm_hours = cohort["ppglm_valid_eeg_hours"]
    onset_rate = cohort["merged_onset_responses_per_hour"]
    positive_seconds = cohort["n_ied_positive_seconds"]
    ppglm_rate = cohort["ied_positive_seconds_per_valid_eeg_hour"]
    full_improvement = 100 * (dependency["dev_B"] - dependency["dev_F"]) / dependency["dev_B"]
    within, between, short_auc = short_kernel_separation()
    repeat = cohort["cross_admission_residual_correlation"].dropna()
    plotted = figure4["figure4_plotted_roc"]
    age = figure4["age_band_aggregate"]
    age_tests = {
        (item["a"], item["b"]): item["p"] for item in figure4["age_band_tests"]
    }
    fractions = population["pooled_fractions"]
    level2 = population["level2"]
    burden = population["c5"]["confirmatory"]
    distance = population["dissimilarity"]

    values = [
        Claim("Cohort", "Participants", "114", f"{len(cohort)}"),
        Claim(
            "Cohort",
            "Table 1 IED-positive seconds",
            "total 3,303,076; median 4,162; range 513–588,593",
            f"total {positive_seconds.sum():,.0f}; median {positive_seconds.median():,.0f}; "
            f"range {positive_seconds.min():,.0f}–{positive_seconds.max():,.0f}",
        ),
        Claim(
            "Cohort",
            "Table 1 IED-positive-second rate",
            "median 49.7/h; range 4.5–1,915/h",
            f"median {ppglm_rate.median():.1f}/h; range {ppglm_rate.min():.1f}–{ppglm_rate.max():,.0f}/h",
        ),
        Claim(
            "Cohort",
            "Reported EEG-support row",
            "80.6 [63.4–117.9] h; range 16.4–302.3 h; total 11,265 h",
            f"{fine_hours.median():.1f} [{ppglm_hours.quantile(.25):.1f}–{ppglm_hours.quantile(.75):.1f}] h; "
            f"range {fine_hours.min():.1f}–{fine_hours.max():.1f} h; total {ppglm_hours.sum():,.0f} h",
        ),
        Claim(
            "Fine kernel",
            "Merged-onset responses",
            "total 1,094,298; median 3,399; range 504–103,544",
            f"total {cohort.n_onset_events.sum():,.0f}; median {cohort.n_onset_events.median():,.0f}; "
            f"range {cohort.n_onset_events.min():,.0f}–{cohort.n_onset_events.max():,.0f}",
        ),
        Claim(
            "Fine kernel",
            "Post-first-onset support",
            "80.6 [58.4–114.2] h; range 16.4–302.3 h",
            f"{fine_hours.median():.1f} [{fine_hours.quantile(.25):.1f}–{fine_hours.quantile(.75):.1f}] h; "
            f"range {fine_hours.min():.1f}–{fine_hours.max():.1f} h",
        ),
        Claim(
            "Fine kernel",
            "Merged-onset response rate",
            "45.1 [17.6–136.6]/h; range 4.2–406.5/h",
            f"{onset_rate.median():.1f} [{onset_rate.quantile(.25):.1f}–{onset_rate.quantile(.75):.1f}]/h; "
            f"range {onset_rate.min():.1f}–{onset_rate.max():.1f}/h",
        ),
        Claim(
            "PP-GLM",
            "Median full-model deviance reduction",
            "20.6%",
            f"{full_improvement.median():.1f}%",
        ),
        Claim(
            "PP-GLM",
            "Pooled standalone H/V/A",
            "97.5% / 17.3% / 6.0%",
            f"{100*fractions['sa_H']['point']:.1f}% / {100*fractions['sa_V']['point']:.1f}% / "
            f"{100*fractions['sa_A']['point']:.1f}%",
        ),
        Claim(
            "PP-GLM",
            "Pooled unique H/V/A",
            "76.7% / 5.8% / −1.6%",
            f"{100*fractions['un_H']['point']:.1f}% / {100*fractions['un_V']['point']:.1f}% / "
            f"{100*fractions['un_A']['point']:.1f}%".replace("-", "−"),
        ),
        Claim(
            "PP-GLM",
            "History exceeds vigilance / ASM",
            "107/114 / 106/114",
            f"{population['contrasts']['sa_H-sa_V']['n_pos']}/114 / "
            f"{population['contrasts']['sa_H-sa_A']['n_pos']}/114",
        ),
        Claim(
            "PP-GLM",
            "Vigilance exceeds ASM after history",
            "77/114; median 0.00073; 95% CI 0.00030–0.00198; P=0.00576",
            f"{level2['n_pos']}/114; median {level2['median']:.5f}; "
            f"95% CI {level2['median_ci95'][0]:.5f}–{level2['median_ci95'][1]:.5f}; "
            f"P={level2['wilcoxon_p']:.5f}",
        ),
        Claim(
            "PP-GLM",
            "Detectable vigilance-positive / ASM signs",
            "95 / +35 and −35",
            f"{detectability['sa_V']['B200_95']['pos']} / "
            f"+{detectability['sa_A']['B2000_95']['pos']} and −{detectability['sa_A']['B2000_95']['neg']}",
        ),
        Claim(
            "Fine kernel",
            "Refractory / peak / late multiplier",
            "3.00 s / 5.00 s at 1.47× / 1.73× over 40–70 s",
            f"{cohort.apparent_refractory_interval_s.median():.2f} s / "
            f"{cohort.peak_lag_s.median():.2f} s at {cohort.peak_multiplier.median():.2f}× / "
            f"{cohort.mean_40_70s_multiplier.median():.2f}× over 40–70 s",
        ),
        Claim(
            "Reproducibility",
            "Ratified 1–15-s split-half correlation",
            "0.965 [0.915–0.987]",
            f"{np.median(within):.3f} [{np.quantile(within,.25):.3f}–{np.quantile(within,.75):.3f}]",
        ),
        Claim(
            "Reproducibility",
            "Between-participant separation",
            "median 0.087 across 12,882 directed pairs; AUC 0.886",
            f"median {np.median(between):.3f} across {between.size:,} directed pairs; AUC {short_auc:.3f}",
        ),
        Claim(
            "Reproducibility",
            "Cross-admission correlation",
            "n=39; 0.905 [0.636–0.987]",
            f"n={len(repeat)}; {repeat.median():.3f} [{repeat.quantile(.25):.3f}–{repeat.quantile(.75):.3f}]",
        ),
        Claim(
            "Figure 4",
            "Plotted ROC values",
            "split-half 0.88 [0.84–0.92]; cross-admission 0.70",
            f"split-half {plotted['auroc']:.2f} [{plotted['ci95'][0]:.2f}–{plotted['ci95'][1]:.2f}]; "
            f"cross-admission {plotted['auroc_cross_admission']:.2f}",
        ),
        Claim(
            "Figure 4",
            "Age-band medians and contrast",
            "0.981 / 0.977 / 0.966; P=0.040",
            f"{age['0-18 y']['median']:.3f} / {age['18-35 y']['median']:.3f} / "
            f"{age['35+ y']['median']:.3f}; P={age_tests[('0-18 y','35+ y')]:.3f}",
        ),
        Claim(
            "Dependency geometry",
            "Burden association",
            "n=108; ρ=−0.122; 95% CI −0.305–0.065; 90% CI −0.275–0.034",
            f"n={burden['n']}; ρ={burden['rho']:.3f}; 95% CI {burden['ci95'][0]:.3f}–{burden['ci95'][1]:.3f}; "
            f"90% CI {burden['ci90'][0]:.3f}–{burden['ci90'][1]:.3f}".replace("-", "−"),
        ),
        Claim(
            "Dependency geometry",
            "All / rate-matched pair distances",
            "1.200 [0.618–2.502], n=6,441 / 0.938 [0.501–2.146], n=210; max 7.27",
            f"{distance['all_pairs']['median']:.3f} [{distance['all_pairs']['iqr'][0]:.3f}–{distance['all_pairs']['iqr'][1]:.3f}], "
            f"n={distance['all_pairs']['n']:,} / {distance['rate_matched_pairs_dlogr_le_0.10']['median']:.3f} "
            f"[{distance['rate_matched_pairs_dlogr_le_0.10']['iqr'][0]:.3f}–{distance['rate_matched_pairs_dlogr_le_0.10']['iqr'][1]:.3f}], "
            f"n={distance['rate_matched_pairs_dlogr_le_0.10']['n']}; max {distance['rate_matched_pairs_dlogr_le_0.10']['max']:.2f}",
        ),
        Claim(
            "Sleep",
            "Stage/wake ratios",
            "N1 1.94 [1.64–2.30], n=112; N2 3.80 [3.25–4.45], n=114; "
            "N3 3.69 [3.07–4.46], n=112; REM 1.50 [1.23–1.82], n=84",
            "; ".join(
                f"{stage.upper()} {sleep[stage]['geomean_ratio']:.2f} "
                f"[{sleep[stage]['geomean_ci95'][0]:.2f}–{sleep[stage]['geomean_ci95'][1]:.2f}], "
                f"n={sleep[stage]['n']}"
                for stage in ("n1", "n2", "n3", "rem")
            ),
        ),
        Claim(
            "Sleep",
            "N2/N1, N3/N1, N3/N2, REM/N2, REM/N3; REM/N1 q",
            "1.95 / 1.89 / 0.96 / 0.42 / 0.43; q=0.051",
            f"{sleep_pairs['n1_vs_n2']['geomean_ratio']:.2f} / "
            f"{sleep_pairs['n1_vs_n3']['geomean_ratio']:.2f} / "
            f"{sleep_pairs['n2_vs_n3']['geomean_ratio']:.2f} / "
            f"{sleep_pairs['n2_vs_rem']['geomean_ratio']:.2f} / "
            f"{sleep_pairs['n3_vs_rem']['geomean_ratio']:.2f}; "
            f"q={sleep_pairs['n1_vs_rem']['wilcoxon_q_BH10']:.3f}",
        ),
        Claim(
            "Sleep",
            "Supplementary Figure S1 adjusted tests",
            "all stage/wake q<0.001; N2/N3 q=0.38; REM/N1 q=0.051",
            f"all stage/wake q<0.001; "
            f"N2/N3 q={sleep_pairs['n2_vs_n3']['wilcoxon_q_BH10']:.2f}; "
            f"REM/N1 q={sleep_pairs['n1_vs_rem']['wilcoxon_q_BH10']:.3f}"
            if all(sleep[stage]["wilcoxon_q_BH"] < 0.001 for stage in ("n1", "n2", "n3", "rem"))
            else "one or more stage/wake q-values >=0.001",
        ),
    ]
    return values


def main() -> int:
    values = claims()
    print("| Section | Statistic | Paper/SI | Reproduced from public data |")
    print("|:--|:--|:--|:--|")
    for claim in values:
        mark = "✓" if claim.matches else "✗"
        print(
            f"| {claim.section} | {mark} {claim.statistic} | "
            f"{claim.reported} | {claim.reproduced} |"
        )
    mismatches = [claim for claim in values if not claim.matches]
    if mismatches:
        print(f"\nFAIL · {len(mismatches)} reported-statistic mismatch(es)")
        return 1
    print(f"\nPASS · {len(values)} manuscript/appendix claim groups reproduced")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
