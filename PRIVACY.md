# Privacy and deidentification

This repository is a derived public result package, not a clinical-data archive. The release was built with an explicit allowlist and then scanned independently at the file, table, archive, PDF-text, and image-text levels.

## Included

- Arbitrary `P###` research labels for cohort-level analytic linkage
- Fitted history curves, confidence intervals, PP-GLM coordinates, and model-evaluation statistics
- State-level exposure and IED-positive-second counts
- Anonymous repeat recordings labeled `A` and `B`
- A relative-time EEG excerpt already used in Figure 1
- Aggregate demographic and recording-site summaries in the published supplement
- Frozen manuscript and supplementary figure renders

## Excluded

- Direct source identifiers and the private crosswalk
- Names, medical record numbers, dates of birth, addresses, contact details, and clinical notes
- Calendar dates or clock timestamps
- Source admission, stay, session, and file identifiers
- Participant-level hospital/site, age, sex, race, or epilepsy metadata tables
- Complete ordered event sequences and full longitudinal EEG/timeline files
- Medication administration records and source pharmacokinetic files
- Local filesystem paths, cloud locations, logs, credentials, and execution environments

Inter-event information is released as 1–90-second histograms rather than ordered sequences. Repeat recordings are renamed within participant. The Figure 1 archive has relative time only and no participant label. Exact age/sex text that is visibly embedded in the frozen manuscript Figure 3 is not repeated in machine-readable data.

## Release gate

Run the public gate with:

```bash
make verify
```

Release managers with access to the private crosswalk should additionally run:

```bash
python scripts/verify_release.py --crosswalk /secure/path/pid_crosswalk.csv
```

The stricter gate compares extracted content against every known source identifier. When available, Tesseract OCR is also applied to all PNG figures. SHA-256 manifests make post-audit changes detectable.

## Governance note

Technical deidentification does not replace institutional review, data-use agreements, or journal policy. Before publishing a fork or adding new variables, obtain the approvals applicable to the underlying study. Do not attempt to re-identify participants or combine these derivatives with external person-level data.

Please report a suspected disclosure privately to the corresponding research team rather than opening a public issue containing the material.
