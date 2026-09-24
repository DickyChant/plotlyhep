# plotlyhep — mplhep, mirrored for Plotly

**Documentation:** https://dickychant.github.io/plotlyhep/ · **Gallery:** https://dickychant.github.io/plotlyhep/gallery/ (ATLAS and CMS Open Data figures with hover that explains each process) · **Editor:** https://dickychant.github.io/plotlyhep/gallery/editor/ (load any figure or your own Plotly JSON, drag things around, export JSON / PNG / SVG or the exact `update_layout` edits).

[mplhep](https://github.com/scikit-hep/mplhep) gives matplotlib the CMS / ATLAS
look. `plotlyhep` gives Plotly the same look — and proves it with pixels.

```python
import numpy as np, plotlyhep as php

php.style.use("CMS")  # Plotly template built from mplhep's own rcParams
fig = php.figure()  # 10 in x 10 in at 100 dpi, like mplhep's CMS figsize
php.histplot(fig, [sig, bkg], bins, label=["Signal", "Background"])  # mplhep-style steps
php.histplot(fig, data, bins, yerr=True, histtype="errorbar", color="black", label="Data")
php.cms.label(fig, "Preliminary", data=True, lumi=138, com=13.6, loc=0)  # CMS Preliminary  138 fb⁻¹ (13.6 TeV)
php.set_xlabel(fig, "m<sub>jj</sub> [GeV]")
php.set_ylabel(fig, "Events / 5 GeV")
fig.show()  # interactive; fig.write_image("plot.png") via kaleido
```

## ROOT too

`plotlyhep.convert.from_root(canvas)` turns a TCanvas (or a single TH1 / TH2 / TGraph / TF1 with
its draw option, or an uproot-read object) into the same figure Plotly-side: pad margins, the
frame, ROOT text sizes, marker and line styles, colours and palette, legend, TLatex, title and
stats boxes, sub-pads. `to_root(fig)` goes back. Checked by pixel diff against ROOT's own
painter (`tests/test_root_convert.py`, run wherever PyROOT is importable).

## Ratio panels

```python
fig = php.ratio_figure("CMS", height_ratios=(3, 1), hspace=0.05)  # matplotlib GridSpec geometry, shared x
php.histplot(fig, mc, bins, label="MC")
php.histplot(fig, data, bins, yerr=True, histtype="errorbar", color="black", label="Data")
php.ratioplot(fig, data, mc, bins, den_w2=mc_w2)  # data/MC ± err, MC stat. band, dashed line at 1
```

## Two ways in

| | |
|---|---|
| **Mirror** (`plotlyhep.style`, `histplot`, `cms.label`, …) | Native Plotly figures that follow the mplhep conventions: fonts, inward ticks on all sides, no grid, colour cycles, the experiment label geometry (`loc` 0–4), right/top-aligned axis labels. Interactive, hover, zoom. |
| **Convert** (`plotlyhep.convert.from_mpl`, `to_mpl`) | Take an existing matplotlib figure (mplhep-styled or not) and rebuild it as a Plotly figure by walking the *drawn* artist tree: lines, step patches, bars, collections, quadmesh/images, every text placed by its rendered bounding box, tick labels copied verbatim, legend. And back. |

```python
from plotlyhep.convert import from_mpl, to_mpl

pfig = from_mpl(mpl_fig)  # matplotlib.figure.Figure -> plotly.graph_objects.Figure
mfig = to_mpl(pfig)  # and back
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
| `from_mpl` of the histogram figure | 7.9 | 4.2 % | 0.905 |
| `from_mpl` → `to_mpl` round trip | 0.04 | 0.02 % | 0.999 |
| main + ratio panel vs matplotlib GridSpec (3:1, hspace 0.05) | 9.7 | 5.4 % | 0.866 |

What the remaining difference is: sub-pixel text rasterisation (two different
text engines), Plotly's slightly heavier line antialiasing, and legend entry
spacing. What it is not: geometry — the axes frame, ticks, labels and
histograms land within 2 px.

## The ROOT tutorial plots, rebuilt

The gallery's headline figures are ROOT's `df102_NanoAODDimuonAnalysis` and
`df106_HiggsToFourLeptons` tutorial plots rebuilt in Plotly from the tutorial
sources (same selection, normalisation, binning, canvas, fonts, label positions,
colours) and compared pixel by pixel with the tutorial's own output images
(`tests/compare_root.py`, ratchet in `tests/thresholds_root.json`):

| plot | canvas | mean abs diff | pixels > 40 | SSIM |
|---|---|---|---|---|
| df102 dimuon spectrum (CMS Open Data, 61.5 M events) | 796 × 672 at 3× | 6.2 | 3.1 % | 0.933 |
| df106 H → ZZ* → 4ℓ (ATLAS Open Data) | 596 × 572 | 11.8 | 6.8 % | 0.816 |

Lessons that came out of it, all in `plotlyhep.root_template` / `docs/root_figures.py`:
ROOT's `SetTextSize(f)` is not the em size (em ≈ 0.90 f·H), its "bottom"
alignment is the baseline, tick lengths are 3 % of the plot area, NDC is the
canvas while Plotly's `paper` is the plot area, `exponentformat="power"`
renders tick labels ~25 % larger than explicit `10<sup>n</sup>` text, and the
high-mass "grass" of a 30 000-bin histogram is ROOT collapsing bins per pixel
column with empty bins drawn at the axis minimum.

## Install

Not on PyPI; install from git, a tag, or the tarball / wheel that CI attaches to every release:

```bash
pip install "plotlyhep @ git+https://github.com/DickyChant/plotlyhep"            # main
pip install "plotlyhep @ git+https://github.com/DickyChant/plotlyhep@v0.1.0"     # a tag
pip install https://github.com/DickyChant/plotlyhep/releases/download/v0.1.0/plotlyhep-0.1.0-py3-none-any.whl
```

Runtime dependencies are `plotly` and `numpy` only. For a development checkout:

```bash
pip install -e ".[dev]"           # test extra pins Plotly 5 + kaleido 0.2.1 (bundled Chromium); the library itself runs on Plotly 5 or 6
pytest                            # 79 tests, ~6 s
mkdocs serve                      # the documentation site
```

## Tests

The suite is laid out like [mplhep's](https://github.com/scikit-hep/mplhep/tree/master/tests)
and follows the [scikit-hep developer guidelines](https://scikit-hep.org/developer)
(`pyproject` metadata and classifiers, `[tool.pytest.ini_options]`, ruff, nox,
pre-commit, a CI matrix over Python 3.10–3.13). Where mplhep uses pytest-mpl,
plotlyhep has an equivalent marker in `tests/conftest.py`:

```python
@pytest.mark.image_compare(tolerance=4, remove_text=True)
def test_histplot_step():
    fig = php.figure()
    php.histplot(fig, [h1, h2], bins, label=["a", "b"])
    return fig  # rendered with kaleido, RMS-compared with tests/baseline/test_histplot_step.png
```

`remove_text=True` strips annotations, titles, tick labels and the legend before
rendering, so baselines test geometry rather than the machine's fonts; the tests
that keep text run with fontconfig pinned to the font files `mplhep-data` ships,
which is what makes the same baselines pass on a laptop and on CI.
`pytest --regen-baselines` rewrites them after an intentional visual change;
failures drop actual / expected / diff images under `tests/output/failed/`.
`CONTRIBUTING.md` lists what each test file covers; the two fidelity harnesses
(`test_pixel.py` against mplhep, `test_root.py` against ROOT's tutorial images)
sit alongside.

## Status

0.1: CMS and ATLAS templates, `histplot` (`step`, `fill`, `errorbar`; `yerr`,
`stack`, `density`), `hist2dplot`, `exp_text` / `exp_label` with `loc` 0–4,
axis-label helpers, ratio panels on matplotlib GridSpec geometry, `from_mpl` /
`to_mpl` for the common artist types, hover carriers, frozen HTML embeds with an
edit chip, the pixel-diff harnesses, a mplhep-style test suite and CI. Not yet:
subplots with shared axes beyond the ratio panel, `band`/`bar`/`barstep`
histtypes, colorbars in `from_mpl`, log-axis minor ticks in `to_mpl`.

Licensed BSD-3-Clause; style values and helper semantics follow mplhep
(BSD-3-Clause, © Andrzej Novak and contributors).
