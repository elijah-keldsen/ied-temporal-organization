# Contributing

Issues and pull requests that improve documentation, accessibility, tests, or reproducibility are welcome.

Before submitting a change:

```bash
make verify
make figures
git status --short
```

Do not add raw clinical data, source identifiers, dates, participant-level demographics/site, full event sequences, local paths, credentials, or a crosswalk. New participant-level fields require a fresh privacy review and institutional authorization. If you suspect a disclosure, report it privately rather than attaching the material to a public issue.

Keep scientific changes separate from presentation-only changes, document altered assumptions, and update both the data dictionary and verification invariants when a public schema changes.
