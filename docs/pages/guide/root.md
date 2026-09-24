# The ROOT look

`root_template` reproduces a `gStyle`-like canvas: Helvetica text with sizes given as
fractions of the pad height as ROOT does, a full frame with ticks on the bottom and left
(or mirrored), tick lengths as a fraction of the plot area, and margins as pad fractions.

```python
import plotly.graph_objects as go
fig = go.Figure(layout=dict(template=php.root_template(800, 600, label_size=0.035, title_size=0.04,
                                                       margins=(0.1, 0.1, 0.1, 0.1), tick_len=0.03)))
```

The [gallery](https://dickychant.github.io/plotlyhep/gallery/) rebuilds two ROOT tutorials, `df102_NanoAODDimuonAnalysis` and
`df106_HiggsToFourLeptons`, on this template from CERN Open Data and compares them to the
reference PNGs on root.cern in the test suite. The lessons from getting those to match are
in the README: ROOT's NDC is not Plotly's paper coordinate system, the `E` draw option
means bin-width horizontal bars without caps, and Plotly's power-of-ten tick labels are
about a quarter larger than ROOT's, so the rebuild writes them explicitly.

## ROOT to Plotly and back

```python
from plotlyhep.convert import from_root, to_root

fig = from_root(canvas)            # a TCanvas or TPad with everything drawn on it
fig = from_root(h, "E1")           # a single TH1 / TH2 / TGraph* / TMultiGraph / THStack / TF1 with a draw option
fig = from_root(uproot_file["h"])  # an object read with uproot, no ROOT installation needed
canvas = to_root(fig)              # back: TH1D / TGraph(Asymm)Errors / TH2D / TLatex / TLine / TLegend on a TCanvas
```

`from_root` reads what ROOT drew: the pad margins become the axis domain, so Plotly's paper
fractions are ROOT's NDC and every NDC-positioned object (legend, TLatex, the title box, a
stats box) lands where ROOT put it. Text sizes are fractions of the pad height as in ROOT,
precision-3 fonts stay in pixels, bold and italic font codes carry over, TLatex markup becomes
HTML (`#it{}`, `_{}`, `^{}`, `#sqrt{}`, Greek letters, accents), marker and line styles map to
their Plotly counterparts, colours come from the live colour table (or a snapshot of it for
uproot objects) and a TH2 uses the current palette. Draw options are honoured: `HIST`, `E`/`E1`
with or without horizontal bars (`X0`), `P`, `L`, `C`, `B`, `COL`/`COLZ`, `APL`, `3` bands,
`NOSTACK`, `SAME`. Fit functions in a histogram's function list are drawn, `Divide`d canvases
become one subplot per pad, and log pads become log axes.

A single object is drawn on a temporary batch canvas first, so ROOT's own axis ranges, title and
stats box apply. `to_root` recognises the traces plotlyhep produces (steps, error bars,
heatmaps, the end-aligned axis labels) and returns the canvas with the objects kept alive on it.

The test suite renders one canvas through ROOT's painter and through `from_root` + kaleido and
ratchets the pixel difference, the same way the gallery rebuilds are checked.
