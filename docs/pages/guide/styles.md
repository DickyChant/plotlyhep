# Styles and figures

Two templates are registered with `plotly.io` on import, `hep_cms` and `hep_atlas`. Their
values are derived from mplhep's rcParams: font family and sizes (points to pixels at
100 dpi), inside mirrored ticks with mplhep's major and minor lengths, no grid, the
experiment colour cycle, the figure size and the subplot margins.

```python
import plotlyhep as php

php.style.use("CMS")          # default template for every new figure, like mplhep.style.use
fig = php.figure()            # go.Figure with the template and the mplhep figure size
fig = php.figure("ATLAS")     # one figure in another style, without changing the default
php.figsize_px("CMS")         # (1000, 1000); ATLAS is (800, 600)
```

`php.figure(**layout)` forwards extra keywords to `go.Figure(layout=...)`. Give it a
`width`/`height` (or `scale=`) and the template is scaled with it: fonts, tick lengths, line
widths and margins shrink together, so `php.figure("CMS", width=600, height=600)` is the
1000 px CMS figure at 60 %, not a 1000 px layout squeezed into 600 px. Slides rarely have
room for the native size; this is how a figure keeps mplhep's proportions at any size.
`php.template("CMS", scale=0.6)` is the same template as an object.

## Templates as data

```python
php.template("CMS")                          # the go.layout.Template object
php.template_json("CMS", transparent=True)   # plain dict for JavaScript: Plotly.newPlot(gd, data, {template: T})
```

`python -m plotlyhep export-templates some/dir` writes `hep_cms.json`, `hep_atlas.json` and
their `_transparent` variants, for a page that draws with plotly.js and no Python at all.

## Axis labels where mplhep puts them

mplhep right-aligns the x label at the end of the axis and top-aligns the y label. Plotly's
axis titles are centred, so these helpers draw the label as an annotation instead:

```python
php.set_xlabel(fig, "m<sub>jj</sub> [GeV]")
php.set_ylabel(fig, "Events / 5 GeV")
```

Text is HTML, not mathtext: `<sub>`, `<sup>`, `<b>`, `<i>` and Unicode (`fb⁻¹`, `√s`).
`php.convert.mathtext_to_html` translates the common `$_{}$` and `$^{}$` cases.
