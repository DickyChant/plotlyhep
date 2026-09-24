"""Embedding Plotly figures in HTML slides (frontend-slides decks) with live, persisted edits.

    from plotlyhep.html import script_tag, embed
    head += script_tag()                                   # once per deck
    slide += embed(fig, "plot-s12", editable=True)         # per figure

With editable=True the presenter can drag annotations, their arrow tails, the legend
and the axis titles in the browser; every change is stored in localStorage under
plot-edits:<div_id> and re-applied on load, so a deck reviewed in the browser keeps
its adjusted annotations. Under navigator.webdriver (the PDF export) nothing is
interactive and the stored edits are still applied, so the export shows them."""
from __future__ import annotations
import json
import plotly.graph_objects as go
from .styles import template_json

PLOTLY_JS = "https://cdn.plot.ly/plotly-2.35.2.min.js"

def script_tag(exp: str | None = "CMS", *, transparent: bool = True) -> str:
    """plotly.js once per deck, plus the experiment template as a page-level theme:
    every figure embedded afterwards (by embed() or by hand) renders with the mplhep look
    unless it carries its own template. This is the deck-level "CSS" for plots."""
    tag = f'<script src="{PLOTLY_JS}" charset="utf-8"></script>'
    if exp:
        tag += f"\n<script>window.PLOTLYHEP_TEMPLATE = {json.dumps(template_json(exp, transparent=transparent), cls=_NumpyEncoder)};</script>"
    return tag

SLIDE_CSS = """<style>
/* plots on slides: transparent ground, the skin's font, no stray scrollbars */
.js-plotly-plot, .plot-container { background: transparent !important; }
.js-plotly-plot .plotly .main-svg { background: transparent !important; }
.js-plotly-plot .plotly text { font-family: inherit; }
</style>"""

def embed(fig: go.Figure, div_id: str, *, editable: bool = True, persist: bool = True,
          width: str = "100%", height: str = "auto", inherit_template: bool = True) -> str:
    """HTML fragment: a div plus the script that draws the figure into it.
    inherit_template=True drops the figure's own template so the page-level
    PLOTLYHEP_TEMPLATE (from script_tag) applies — one theme for the whole deck."""
    j = fig.to_plotly_json()
    if inherit_template: j["layout"].pop("template", None)
    data = json.dumps(j["data"], cls=_NumpyEncoder)
    layout = json.dumps(j["layout"], cls=_NumpyEncoder)
    config = {"displayModeBar": False, "responsive": True, "editable": editable,
              "edits": {"annotationPosition": True, "annotationTail": True, "annotationText": True,
                        "legendPosition": True, "axisTitleText": True, "titleText": True}}
    persist_js = f"""
      var key = 'plot-edits:' + '{div_id}';
      var saved = {{}}; try {{ saved = JSON.parse(localStorage.getItem(key) || '{{}}'); }} catch (e) {{}}
      Plotly.newPlot(gd, data, layout, config).then(function () {{
        if (Object.keys(saved).length) Plotly.relayout(gd, saved);
        gd.on('plotly_relayout', function (e) {{
          Object.assign(saved, e); try {{ localStorage.setItem(key, JSON.stringify(saved)); }} catch (err) {{}}
        }});
      }});""" if persist else "      Plotly.newPlot(gd, data, layout, config);"
    return f"""<div id="{div_id}" style="width:{width}; height:{height};"></div>
<script>
(function () {{
  var gd = document.getElementById('{div_id}');
  var data = {data}, layout = {layout}, config = {json.dumps(config)};
  if (window.PLOTLYHEP_TEMPLATE && !layout.template) layout.template = window.PLOTLYHEP_TEMPLATE;
  if (navigator.webdriver) {{ config.editable = false; config.staticPlot = true; }}
{persist_js}
}})();
</script>"""

class _NumpyEncoder(json.JSONEncoder):
    def default(self, o):
        try:
            import numpy as np
            if isinstance(o, np.ndarray): return o.tolist()
            if isinstance(o, (np.integer,)): return int(o)
            if isinstance(o, (np.floating,)): return float(o)
        except ImportError:
            pass
        return super().default(o)
