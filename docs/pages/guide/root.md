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
