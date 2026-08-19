# Manuscript–repository results checklist

This checklist maps the numerical claims in the Brain manuscript and supplementary appendix to deidentified files in this repository. Run `make statistics` to recompute the displayed values and `make verify` to enforce them as release gates.

## Response and exposure accounting

Two response definitions are intentionally separate:

| Analysis | Response | Public fields |
|:--|:--|:--|
| Primary 10-second PP-GLM and sleep-density analysis | Detector-positive one-second intervals | `n_ied_positive_seconds`, `ied_positive_seconds_per_valid_eeg_hour` |
| Fine-resolution history kernel | First second of each merged IED run | `n_onset_events`, `merged_onset_responses_per_hour` |

The 3,303,076 total, 4,162 median, and 49.7/h median in main Table 1 refer to IED-positive seconds. The fine-kernel totals are 1,094,298 merged onsets and a median of 3,399 per participant. The public cohort table keeps both denominators explicit: `ppglm_valid_eeg_hours` for the primary model and `fine_kernel_post_first_onset_hours` for the fine kernel.

## Numerical crosswalk

| Manuscript or SI result | Reported value | Public source |
|:--|:--|:--|
| Cohort size | 114 | `cohort_features.csv` |
| Full-model median held-out deviance reduction | 20.6% | `dependency_coordinates.csv` |
| Pooled standalone history / vigilance / ASM fractions | 97.5% / 17.3% / 6.0% | `population_inference.json` |
| Pooled unique history / vigilance / ASM fractions | 76.7% / 5.8% / −1.6% | `population_inference.json` |
| History exceeds vigilance / ASM | 107/114 / 106/114 | `population_inference.json` |
| Vigilance exceeds ASM after history | 77/114; median 0.00073; *P*=0.00576 | `population_inference.json` |
| Detectable vigilance-positive / ASM-positive / ASM-negative contributions | 95 / 35 / 35 | `detectability_summary.json` |
| Refractory interval / rebound peak / late multiplier | 3.00 s / 5.00 s at 1.47× / 1.73× | `cohort_features.csv` |
| Split-half residual correlation | 0.965 [0.915–0.987] | `manuscript_short_history_curves.csv.gz` |
| Between-participant residual correlation and separation | median 0.087 across 12,882 directed pairs; AUC 0.886 | `manuscript_short_history_curves.csv.gz` |
| Cross-admission residual correlation | 0.905 [0.636–0.987], *n*=39 | `cohort_features.csv` |
| Figure 4 plotted split-half / cross-admission ROC | 0.88 [0.84–0.92] / 0.70 | `figure4_roc_curves.csv`, `figure4_summary.json` |
| Burden–dependency association | ρ=−0.122, *n*=108 | `population_inference.json` |
| All-pair / rate-matched dependency distance | 1.200 / 0.938 | `population_inference.json` |
| N1 / N2 / N3 / REM density relative to wake | 1.94 / 3.80 / 3.69 / 1.50 | `sleep_density_ae114.json` |

## Why two split-half AUC values appear

The manuscript Results and Supplementary Figure S2 report `0.886` for the ratified 1–15-second analysis. It compares 114 within-participant split-half residual correlations with 12,882 directed cross-half, between-participant correlations using the cohort mean short-kernel template.

Main Figure 4 uses a related display analysis over the 1–90-second curves. Its negative set contains 6,441 unordered first-half pairs, and its residual template is re-estimated with both tested participants left out. Its exact AUC is `0.881574`, printed as `0.88` in the figure, with a participant-resampled 95% interval of `0.84–0.92`. The cross-admission curve has AUC `0.703346`, printed as `0.70`. These values are separate estimands rather than alternative rounding of one calculation.

## Detectability bootstrap counts

The manuscript's 95 vigilance-positive count uses the 200-replicate interval recorded as `B200_95`. Figure 2's four-class profile uses the more stable 2,000-replicate intervals (`B2000_95`), yielding 62 both-detectable, 39 vigilance-only, 8 ASM-only, and 5 neither. ASM-positive and ASM-negative counts are 35/35 under both settings.

All checks operate only on deidentified participant labels and aggregate result files.
