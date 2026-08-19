# Reproducibility

This is a result-level reproducibility package. It supports inspection of every headline statistic and regeneration of public-safe versions of Figures 2, 3, 4, 6, and Supplementary Figure S3 without controlled clinical data.

## Environment

Python 3.10 or later is recommended.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Validate the release

```bash
make verify
```

The verifier checks:

1. cohort sizes, response totals, response-unit semantics, and history-curve grids;
2. manuscript-defining PP-GLM fractions, detectability classes, ASM sign split, ROC AUCs, and sleep ratios;
3. required figures, appendix files, SHA-256 provenance, and stale terminology;
4. prohibited columns, identifier-shaped tokens, dates, filesystem paths, cloud locations, and credential patterns.

## Regenerate figures

```bash
make figures
```

This writes deterministic PNGs under `figures/reproduced/`. These public-safe renderings intentionally omit participant-level demographics and ordered event rugs while preserving the plotted model quantities.

Regenerate the terminology-aligned supplementary correlation matrix with:

```bash
make supplement-figure
```

## Reproducibility tiers

| Tier | Included here | Requires controlled source data |
|:--|:--:|:--:|
| Reported cohort statistics and model comparisons | Yes | No |
| History and repeat-recording curves | Yes | No |
| Figures 2, 3, 4, 6 and Supplementary Figure S3 | Yes | No |
| Figure 1 displayed relative-time excerpt | Yes | No |
| Full Figure 1 admission reconstruction from source timelines | No | Yes |
| Figure 5 full spectrogram/timeline reconstruction | No | Yes |
| Detector execution, sleep staging, pharmacokinetic estimation, and model refitting from clinical timelines | No | Yes |

The frozen manuscript figure renders are included so that exact page-ready artifacts remain available even where raw clinical inputs cannot be redistributed.

## Determinism and provenance

Plot jitter uses fixed NumPy seeds. Frozen artifacts are recorded in `provenance/source_artifact_hashes.json`; the whole repository is recorded in `provenance/release_manifest.json`. The latter can be refreshed only after a clean gate:

```bash
python scripts/verify_release.py --write-manifest
```
