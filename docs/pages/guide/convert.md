# matplotlib to Plotly and back

```python
from plotlyhep import convert

pfig = convert.from_mpl(mpl_fig)       # walk the drawn artists into a go.Figure
mfig = convert.to_mpl(pfig)            # and back
```

`from_mpl` reads what matplotlib actually drew: lines (with dash styles), step patches from
`mplhep.histplot`, error-bar containers (into `error_y`), patches, collections, images, texts
placed by their window extent, arrow annotations (standoff and shrink converted), the legend
with its order kept through `legendrank`, and the axes' ranges, tick positions and labels,
including log scales and minor ticks. Sizes convert at the figure's dpi, so a 10×10 inch
figure at 100 dpi becomes a 1000×1000 px figure whose text is the same size on screen.

`to_mpl` does the reverse for the trace types Plotly produces from the helpers here: scatter
lines and markers, `hv` steps, bars, error bars, heatmaps, annotations as texts or arrows.

The round trip is tested by pixel diff: `mplhep → from_mpl → to_mpl` renders within
0.05 grey levels of the original on average. `mathtext_to_html` and `html_to_mathtext` bridge
the two text markups for the common sub- and superscript cases.

Use it when a plot already exists as matplotlib code and you want the live, hoverable version
on a slide; write the plot with plotlyhep directly when you want per-bin hover, because a
converted line carries no bin contents.
