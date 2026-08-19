# Provenance

The release was assembled from the frozen `onset_pen1_ge500_ae114` result cohort and the manuscript-aligned supplementary appendix. The authoritative manuscript cohort contains 114 participants selected for at least 500 merged IED onsets and estimable model inputs.

## Transformations

1. Source identifiers were replaced with stable `P###` labels using a private crosswalk that is not present here.
2. Clinical timeline data were reduced to figure-ready model derivatives, relative-time context, and state-level totals.
3. Repeat-recording identifiers were replaced with `A` and `B`; full event sequences were reduced to interval histograms.
4. Participant-level demographics and site were withheld; aggregate supplement summaries were retained.
5. PP-GLM result tables were copied after identifier remapping and removal of execution-time fields.
6. Supplement table headers were normalized to manuscript-authoritative response and reproducibility terminology.
7. Ratified 1–15-second kernels underlying the manuscript/SI separation statistics were exported separately from the extended 1–90-second curves used by Figures 1, 3, and 4.
8. Every frozen image, appendix, and source artifact was hashed at copy time.

`provenance/source_artifact_hashes.json` records the source and release SHA-256 digest for each copied publication artifact without exposing private source paths. `provenance/release_manifest.json` records the complete public tree.

## Response units

Two related response definitions appear in the analysis:

- The one-second PP-GLM uses **IED-positive seconds**. The manuscript Table 1 total of 3,303,076 and median of 4,162 refer to this detector-positive-second quantity.
- Eligibility and fine-resolution history kernels use **merged onset events**. Their public cohort total is 1,094,298 and median is 3,399.

Public field names preserve that distinction explicitly.

The public cohort table also preserves two exposure denominators: PP-GLM valid EEG hours and fine-kernel post-first-onset hours. [RESULTS_CHECKLIST.md](RESULTS_CHECKLIST.md) records which denominator supports each reported statistic.
