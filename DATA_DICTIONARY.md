# Data dictionary

All participant-level files use arbitrary `P###` research labels. The mapping to source identifiers is not included. Blank values represent quantities that were not estimable or not applicable; they are not encoded as zero.

## Cohort overview

### `data/deidentified/cohort_features.csv`

One row per participant (`n = 114`).

| Field | Meaning |
|:--|:--|
| `participant_id` | Arbitrary public identifier |
| `n_onset_events` | Merged IED onset events used by the fine-resolution history model |
| `n_ied_positive_seconds` | One-second bins containing one or more detector-positive samples; this is the response unit used by the 1-second PP-GLM |
| `modeled_hours_after_first_onset` | Analyzable hours after the first onset within each gap-aware segment |
| `n_stays_fit` | Number of qualifying recording stays used for history fitting |
| `asm_estimable` | Whether model-estimated ASM exposure was estimable |
| `modeled_onset_rate_per_hour` | Merged onset count divided by post-first-onset modeled hours |
| `apparent_refractory_interval_s` | Initial interval whose upper 95% curve bound remains below baseline |
| `peak_lag_s` | Lag of maximum fitted multiplier in the significant excitatory interval |
| `peak_multiplier` | Maximum fitted rate multiplier in that interval |
| `mean_40_70s_multiplier` | Mean fitted multiplier over 40–70 seconds |
| `split_half_residual_correlation` | Residual correlation between independently fit alternating-clock-hour halves |
| `cross_admission_residual_correlation` | Residual correlation between qualifying admissions; present for 39 participants |

The manuscript Table 1 labels the 4,162 median and 3,303,076 total as IEDs/spikes. In this release those quantities are named explicitly as `n_ied_positive_seconds`; the separate merged-onset median is 3,399.

## History curves

### `data/deidentified/history/history_curves.csv.gz`

One row per participant and 0.5-second evaluation lag from 1–90 seconds (`114 × 179` rows).

| Field | Meaning |
|:--|:--|
| `full_multiplier` | Full-record history rate multiplier |
| `lower_95`, `upper_95` | Pointwise delta-method 95% confidence interval |
| `split_a_multiplier`, `split_b_multiplier` | Independently estimated alternating-clock-hour half curves |
| `figure3_example` | Display order for Figure 3; blank for non-exemplars |

### `inter_event_interval_histograms.csv.gz`

Per-participant counts of within-segment inter-onset intervals from 1–90 seconds. Only histograms are released; event order and absolute event times are not.

### `repeat_recording_curves.csv.gz`

History curves for 39 participants with two qualifying recordings. Recordings are labeled `A` and `B`; source stay identifiers and dates are removed. Each curve includes its 95% confidence interval, onset count, and recorded duration.

### Figure 3 and Figure 4 files

- `figure3_examples.json` contains public labels and history-curve summary features; age and sex are intentionally omitted.
- `figure4_summary.json` contains the four displayed participants, morphology agreement metrics, ROC summaries, and aggregate age-band results.
- `figure4_roc_curves.csv` contains the two ROC traces shown in Figure 4.

## PP-GLM outputs

Files under `data/deidentified/ppglm/` retain the frozen numeric columns while replacing `pid` with `participant_id` and removing execution-time fields.

| File | Contents |
|:--|:--|
| `dependency_coordinates.csv` | Held-out standalone and unique history (`H`), vigilance (`V`), and ASM (`A`) coordinates; response counts/rates are named explicitly as IED-positive seconds |
| `bootstrap_detectability.csv` | Participant block-bootstrap intervals at 200 and 2,000 replicates |
| `cross_validated_models_lambda*.csv` | Eight-model held-out deviance results across the regularization sensitivity band |
| `heldout_auroc.csv` | Held-out discrimination for each nested model |
| `regularization_sensitivity.csv` | Cohort-level pooled fractions at each penalty |
| `stay_partition_sensitivity.csv` | Participant-level concatenated-versus-partitioned stay comparison |
| `population_inference.json` | Frozen cohort bootstrap summaries, contrasts, and correlations |
| `detectability_summary.json`, `heldout_auroc_summary.json`, `stay_partition_summary.json` | Aggregate checks reported in the appendix |

Abbreviations follow the manuscript model family: `B`, baseline; `H`, recent IED history; `V`, vigilance; `A`, model-estimated ASM exposure; `F`, full model; `sa`, standalone; `un`, unique.

## Sleep-state density

### `data/deidentified/sleep_state_densities.csv`

One row per participant. For each of Wake, N1, N2, N3, and REM, the table gives exposure seconds, IED-positive seconds, and absolute density per minute. Hard vigilance state is the maximum of the five model probabilities in each 10-second bin.

### Summary JSON files

- `sleep_density_ae114.json` contains the four stage-versus-wake geometric-mean ratios, bootstrap confidence intervals, and Benjamini–Hochberg-adjusted tests.
- `sleep_density_pairwise_ae114.json` contains all ten pairwise vigilance-state contrasts.

## Figure 1 relative-time excerpt

### `data/deidentified/figure1/relative_90s_window.npz`

A compressed NumPy archive containing the displayed 90-second EEG excerpt, sampling frequency, channel labels, relative event seconds, hard sleep stage, four model-predicted IED-positive-second rates, ASM concentration traces, and the fitted history curve. It contains no participant ID or calendar timestamp.

### `relative_admission_context.csv.gz`

The displayed admission context on a relative-hour axis: smoothed IED density, sleep stage, and modeled concentrations. Sessions are sequential anonymous integers; source stay/session identifiers are absent.

## Supplement source tables

Files under `supplement/source/tables/` are aggregate matrices and summaries used for Supplementary Figures S2–S4. Response and reproducibility labels have been normalized to the manuscript-authoritative terms “post-first-onset hours” and “split-half residual correlation.”
