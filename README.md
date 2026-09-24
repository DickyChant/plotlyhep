# plotlyhep — mplhep, mirrored for Plotly

[mplhep](https://github.com/scikit-hep/mplhep) gives matplotlib the CMS / ATLAS
look. `plotlyhep` gives Plotly the same look — and proves it with pixels.

```python
import numpy as np, plotlyhep as php

php.style.use("CMS")                       # Plotly template built from mplhep's own rcParams
fig = php.figure()                         # 10 in x 10 in at 100 dpi, like mplhep's CMS figsize
php.histplot(fig, [sig, bkg], bins, label=["Signal", "Background"])          # mplhep-style steps
php.histplot(fig, data, bins, yerr=True, histtype="errorbar", color="black", label="Data")
php.cms.label(fig, "Preliminary", data=True, lumi=138, com=13.6, loc=0)      # CMS Preliminary  138 fb⁻¹ (13.6 TeV)
php.set_xlabel(fig, "m<sub>jj</sub> [GeV]"); php.set_ylabel(fig, "Events / 5 GeV")
fig.show()                                 # interactive; fig.write_image("plot.png") via kaleido
```

## Two ways in

| | |
|---|---|
| **Mirror** (`plotlyhep.style`, `histplot`, `cms.label`, …) | Native Plotly figures that follow the mplhep conventions: fonts, inward ticks on all sides, no grid, colour cycles, the experiment label geometry (`loc` 0–4), right/top-aligned axis labels. Interactive, hover, zoom. |
| **Convert** (`plotlyhep.convert.from_mpl`, `to_mpl`) | Take an existing matplotlib figure (mplhep-styled or not) and rebuild it as a Plotly figure by walking the *drawn* artist tree: lines, step patches, bars, collections, quadmesh/images, every text placed by its rendered bounding box, tick labels copied verbatim, legend. And back. |

```python
from plotlyhep.convert import from_mpl, to_mpl
pfig = from_mpl(mpl_fig)          # matplotlib.figure.Figure -> plotly.graph_objects.Figure
mfig = to_mpl(pfig)               # and back
```

## Ground truth is a pixel diff

`tests/compare.py` renders the same content through mplhep (matplotlib, Agg)
and through plotlyhep (Plotly → kaleido) on identical pixel grids — 10 in × 10 in
at 100 dpi = 1000 × 1000 — and compares them: mean absolute difference (grey
levels), fraction of pixels differing by more than 40, and SSIM. Side-by-side
and difference images land in `tests/output/`. `tests/test_pixel.py` is a
ratchet against `tests/thresholds.json`: tighten it when the mirror improves,
never loosen it without a reason in the commit.

Current state (TeX Gyre Heros available to both renderers):

| case | mean abs diff | pixels > 40 | SSIM |
|---|---|---|---|
| empty axes + CMS label | 5.1 | 2.6 % | 0.936 |
| step histograms + data + legend | 7.3 | 4.2 % | 0.900 |
| filled histogram, label inside (`loc=2`) | 5.9 | 3.1 % | 0.921 |
| `from_mpl` of the histogram figure | 7.7 | 4.1 % | 0.906 |
| `from_mpl` → `to_mpl` round trip | 0.17 | 0.09 % | 0.997 |

What the remaining difference is: sub-pixel text rasterisation (two different
text engines), Plotly's slightly heavier line antialiasing, and legend entry
spacing. What it is not: geometry — the axes frame, ticks, labels and
histograms land within 2 px.

## Install

```bash
pip install -e ".[test]"          # kaleido 0.2.1 (bundled Chromium), matplotlib, mplhep, scikit-image, pytest
sudo apt-get install fonts-texgyre  # or any way of giving Chromium the TeX Gyre Heros face mplhep uses
pytest -q tests
```

## Status

0.1: CMS and ATLAS templates, `histplot` (`step`, `fill`, `errorbar`; `yerr`,
`stack`, `density`), `hist2dplot`, `exp_text` / `exp_label` with `loc` 0–4,
axis-label helpers, `from_mpl` / `to_mpl` for the common artist types, the
pixel-diff harness and CI. Not yet: subplots with shared axes, ratio panels,
`band`/`bar`/`barstep` histtypes, colorbars in `from_mpl`, log-axis minor ticks
in `to_mpl`.

Licensed BSD-3-Clause; style values and helper semantics follow mplhep
(BSD-3-Clause, © Andrzej Novak and contributors).
