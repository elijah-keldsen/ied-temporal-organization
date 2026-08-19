PYTHON ?= python3

.PHONY: verify statistics figures supplement-figure supplement-pdf all

verify:
	$(PYTHON) scripts/verify_release.py

statistics:
	$(PYTHON) scripts/reproduce_statistics.py

figures:
	$(PYTHON) scripts/reproduce_figures.py

supplement-figure:
	$(PYTHON) supplement/source/make_aligned_kernel_feature_figure.py

supplement-pdf:
	mkdir -p supplement/source/build
	cd supplement/source && latexmk -xelatex -interaction=nonstopmode -halt-on-error -output-directory=build supplementary_appendix.tex

all: verify statistics figures supplement-figure
