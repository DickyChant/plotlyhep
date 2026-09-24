# plotlyhep

The [mplhep](https://github.com/scikit-hep/mplhep) look for [Plotly](https://plotly.com/python/):
CMS and ATLAS styles, experiment labels, histogram and ratio-panel helpers, per-bin hover,
one-line embedding into HTML slides, and a converter between matplotlib and Plotly figures.
Fidelity is checked by pixel diff against mplhep and against ROOT's own tutorial output,
not asserted.

```python
import numpy as np
import plotlyhep as php

php.style.use("CMS")
bins = np.linspace(0, 200, 41)
mc = np.histogram(np.random.default_rng(1).normal(90, 25, 3000), bins)[0] * 1.3
data = np.histogram(np.random.default_rng(2).normal(90, 25, 4000), bins)[0]

fig = php.figure()
php.histplot(fig, mc, bins, label="MC")
php.histplot(fig, data, bins, yerr=True, histtype="errorbar", color="black", label="Data")
php.cms.label(fig, "Preliminary", data=True, lumi=138, com=13.6)
php.set_xlabel(fig, "m<sub>jj</sub> [GeV]")
php.set_ylabel(fig, "Events")
fig.show()
```

That figure, live (hover a bin):

--8<-- "_snippets/hello.html"

## Where to go

- [Install](install.md) — from git, a tag or a release tarball.
- [Guide](guide/styles.md) — every feature with an example.
- [Gallery](https://dickychant.github.io/plotlyhep/gallery/) — ATLAS and CMS Open Data figures with hover that explains each process, rebuilt to match ROOT's tutorial output, and an [editor](https://dickychant.github.io/plotlyhep/gallery/editor/) that loads any of them or your own Plotly JSON.
- [API reference](api.md) — every public function.

## What it mirrors

| mplhep | plotlyhep |
|---|---|
| `hep.style.use("CMS")` | `php.style.use("CMS")` |
| `plt.subplots(figsize=hep.style.CMS["figure.figsize"])` | `php.figure("CMS")` (1000×1000 px, the same size at 100 dpi) |
| `hep.histplot(H, bins, histtype=..., yerr=..., stack=...)` | `php.histplot(fig, H, bins, ...)` |
| `hep.hist2dplot(H, xbins, ybins)` | `php.hist2dplot(fig, H, xbins, ybins)` |
| `hep.cms.label("Preliminary", data=True, lumi=138, com=13.6, loc=0)` | `php.cms.label(fig, "Preliminary", data=True, lumi=138, com=13.6, loc=0)` |
| `ax.set_xlabel(..., loc="right")` | `php.set_xlabel(fig, ...)` |
| `plt.subplots(2, 1, gridspec_kw=dict(height_ratios=(3, 1), hspace=0.05))` | `php.ratio_figure("CMS", height_ratios=(3, 1), hspace=0.05)` |
