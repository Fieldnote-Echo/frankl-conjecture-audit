# Frankl Conjecture Audit

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20800102.svg)](https://doi.org/10.5281/zenodo.20800102)

Source package for a preprint auditing two claimed proof mechanisms for Frankl's union-closed sets conjecture and recording structural reductions for minimum counterexamples.

The paper does not claim a proof of Frankl's conjecture. It gives explicit finite counterexamples to two proposed proof mechanisms, plus independently checkable structural lemmas for the minimum-counterexample route.

## Contents

- `frankl-conjecture-audit.tex` - top-level paper source
- `frankl-conjecture-audit.bbl` - generated bibliography used for source-package builds
- `references.bib` - bibliography database
- `anc/verify_counterexamples.py` - standard-library Python verifier for the A2 and Schrader counterexamples
- `00README` - source build descriptor
- `LICENSE` - Creative Commons Attribution 4.0 International

## Reproduce

```sh
pdflatex frankl-conjecture-audit.tex
bibtex frankl-conjecture-audit
pdflatex frankl-conjecture-audit.tex
pdflatex frankl-conjecture-audit.tex
python3 anc/verify_counterexamples.py --trace --exhaustive
```

Author: Nelson Daniel Spence, Project Navi.
