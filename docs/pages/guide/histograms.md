# Histograms and hover

`histplot` takes counts and bin edges, like `mplhep.histplot`, and draws one or several
histograms at once:

```python
php.histplot(fig, H, bins)                                     # step outline, edges down to zero
php.histplot(fig, [H1, H2], bins, label=["Z", "tt"], stack=True, histtype="fill")
php.histplot(fig, data, bins, yerr=True, histtype="errorbar", color="black", label="Data")
php.histplot(fig, H, bins, density=True)                       # normalised to unit area
php.histplot(fig, H, bins, yerr=err_array)                     # your own errors
```

| keyword | meaning |
|---|---|
| `histtype` | `"step"` (default), `"fill"`, `"errorbar"` |
| `yerr` | `True` for √N, or an array / list of arrays |
| `stack` | cumulative sums; fills are painted top-down so every layer stays visible, the legend keeps your order |
| `density` | divide by the integral |
| `edges` | `False` to drop the vertical edges at the first and last bin |
| `label`, `color`, `linewidth` | one value or one per histogram |
| `row=2` | draw into the lower panel of a [ratio figure](ratio.md) |

Line widths and marker sizes are mplhep's points converted to pixels at 100 dpi, so a
`step` histogram is 1.5 pt wide here as there.

## Hover

Every bin answers the cursor with its edges, content and error:

```
[80, 85)
412 ± 20.3
```

The drawn outline, fill or error segments never respond themselves (`hoverinfo="skip"`); a
transparent marker sits at each bin centre and carries the `customdata` and `hovertemplate`.
That is why hovering a stacked histogram tells you about the layer under the cursor and not
about the outline above it. `php.plot.bin_hover(edges, values, err, name)` returns the same
`customdata`/`hovertemplate` pair for a trace you build yourself, and any Plotly
`hovertemplate` you pass through `**kw` overrides it.

## 2D histograms

```python
H, xe, ye = np.histogram2d(x, y, bins=[40, 30])
php.hist2dplot(fig, H, xe, ye, colorscale="Viridis")
```

`H` is indexed `[x, y]` as `numpy.histogram2d` returns it; the heatmap shows bin edges on hover.
