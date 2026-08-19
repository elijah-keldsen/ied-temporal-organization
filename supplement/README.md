# Supplementary appendix

`supplementary_appendix.pdf` is the frozen manuscript-aligned appendix. Its editable TeX, aggregate tables, and figure-generation source are under `source/`.

The public TeX differs from the frozen source only in relative figure paths. If XeLaTeX and `latexmk` are installed, rebuild it with:

```bash
make supplement-pdf
```

The rebuild is written to `supplement/source/build/` and does not overwrite the frozen PDF. Supplementary Figure S3 can be regenerated independently with `make supplement-figure`.
