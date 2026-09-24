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
/* frozen figures carry a small chip that toggles edit mode */
.plotlyhep-wrap { position: relative; display: inline-block; max-width: 100%; }
.plotlyhep-chip { position: absolute; right: 8px; top: 6px; z-index: 5; display: flex; gap: 6px;
  font: 12px/1 "IBM Plex Mono", Menlo, Consolas, monospace; letter-spacing: .04em; }
.plotlyhep-chip button { padding: 4px 9px; border: 1px solid rgba(25,28,32,.3); border-radius: 4px;
  background: rgba(255,255,255,.92); color: #191c20; cursor: pointer; font: inherit; }
.plotlyhep-chip button:hover { background: #fff; border-color: rgba(25,28,32,.6); }
.plotlyhep-wrap.editing .plotlyhep-chip button.edit { background: #1a4480; color: #fff; border-color: #1a4480; }
</style>"""

def embed(fig: go.Figure, div_id: str, *, editable: bool = True, persist: bool = True,
          width: str = "100%", height: str = "auto", inherit_template: bool = True,
          frozen: bool = True) -> str:
    """HTML fragment: a div plus the script that draws the figure into it.

    frozen=True (default): the figure behaves like a picture — hover and its own
    buttons/dropdowns work, but no zoom, pan, drag or editing — and carries a small
    "edit" chip that switches editing on (drag annotations, legend, axis titles,
    zoom) and back to "done"; "reset" discards the saved edits. editable=True keeps
    the chip; editable=False removes it. frozen=False starts in the editing state.
    inherit_template=True drops the figure's own template so the page-level
    PLOTLYHEP_TEMPLATE (from script_tag) applies — one theme for the whole deck."""
    j = fig.to_plotly_json()
    if inherit_template: j["layout"].pop("template", None)
    data = json.dumps(j["data"], cls=_NumpyEncoder)
    layout = json.dumps(j["layout"], cls=_NumpyEncoder)
    config_edit = {"displayModeBar": True, "displaylogo": False, "responsive": True, "editable": True, "scrollZoom": True,
                   "edits": {"annotationPosition": True, "annotationTail": True, "annotationText": True,
                             "legendPosition": True, "axisTitleText": True, "titleText": True}}
    config_frozen = {"displayModeBar": False, "responsive": True, "editable": False, "scrollZoom": False, "doubleClick": False}
    start_edit = "true" if (editable and not frozen) else "false"
    chip = ('<div class="plotlyhep-chip"><button class="edit" type="button">edit</button>'
            '<button class="reset" type="button" hidden>reset</button></div>') if editable else ""
    persist_js = f"""
      var key = 'plot-edits:' + '{div_id}';
      var saved = {{}}; try {{ saved = JSON.parse(localStorage.getItem(key) || '{{}}'); }} catch (e) {{}}
      function remember(e) {{ Object.assign(saved, e); try {{ localStorage.setItem(key, JSON.stringify(saved)); }} catch (err) {{}} }}
      function forget() {{ saved = {{}}; try {{ localStorage.removeItem(key); }} catch (err) {{}} }}""" if persist else """
      var saved = {}; function remember(e) { Object.assign(saved, e); } function forget() { saved = {}; }"""
    return f"""<div class="plotlyhep-wrap" style="width:{width};"><div id="{div_id}" style="width:100%; height:{height};"></div>{chip}</div>
<script>
(function () {{
  var gd = document.getElementById('{div_id}'), wrap = gd.parentNode;
  var data = {data}, layout = {layout};
  var configEdit = {json.dumps(config_edit)}, configFrozen = {json.dumps(config_frozen)};
  if (window.PLOTLYHEP_TEMPLATE && !layout.template) layout.template = window.PLOTLYHEP_TEMPLATE;
  var editing = {start_edit};
  if (navigator.webdriver) {{ editing = false; configFrozen.staticPlot = true; }}     // PDF export: a picture
{persist_js}
  var chip = wrap.querySelector('.plotlyhep-chip');
  function paint() {{
    var frozenLayout = editing ? layout : Object.assign({{}}, layout, {{dragmode: false}});
    return Plotly.react(gd, data, frozenLayout, editing ? configEdit : configFrozen).then(function () {{
      if (Object.keys(saved).length) Plotly.relayout(gd, saved);
      wrap.classList.toggle('editing', editing);
      if (chip) {{ chip.querySelector('.edit').textContent = editing ? 'done' : 'edit'; chip.querySelector('.reset').hidden = !editing; }}
    }});
  }}
  paint().then(function () {{
    gd.on('plotly_relayout', function (e) {{ if (editing) remember(e); }});
  }});
  if (chip) {{
    chip.querySelector('.edit').addEventListener('click', function () {{ editing = !editing; paint(); }});
    chip.querySelector('.reset').addEventListener('click', function () {{ forget(); paint(); }});
  }}
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
