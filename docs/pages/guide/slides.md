# Figures in HTML slides

plotlyhep was written for HTML talks: a figure on a slide should be the live Plotly object,
not a screenshot, and it should look like every other figure in the deck.

```python
from plotlyhep import html

head = html.script_tag("CMS")          # plotly.js once per page + the CMS template as a page-level theme
css = html.SLIDE_CSS                   # sizing and the edit chip
slide = html.embed(fig, "fig-mjj")     # a div and the script that draws into it
```

`embed` returns an HTML fragment. What it does by default:

- **Frozen.** The figure does not zoom, pan or drag until the viewer clicks the small
  `edit` chip in its corner; `done` freezes it again and `reset` discards the edits. So a
  stray scroll during a talk moves the slide, not the axes. `frozen=False` starts editable,
  `editable=False` removes the chip.
- **Edits persist.** Dragged annotations and legend positions are kept in `localStorage`
  under `plot-edits:<div_id>` and reapplied on reload (`persist=False` to switch off).
- **The page theme wins.** With `inherit_template=True` the figure's own template is dropped
  and `window.PLOTLYHEP_TEMPLATE` from `script_tag` applies, so switching the deck between
  CMS and ATLAS restyles every figure. `script_tag(None)` publishes no template.
- **Transparent.** `script_tag(exp, transparent=True)` makes paper and plot backgrounds
  transparent so the slide background shows through.

`width` and `height` are CSS lengths for the container (`"100%"` and `"auto"` by default,
`auto` keeps the figure's own aspect ratio).

!!! tip "In the frontend-slides skill"
    The [frontend-slides](https://github.com/DickyChant/frontend-slides) deck engine carries
    plotlyhep as a submodule and documents this workflow under "Plots for slides".
