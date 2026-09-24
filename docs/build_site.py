"""Build the GitHub Pages site from the harness: interactive figures (hover, editable
annotations), every pixel comparison with its numbers, and the page-level theme demo.
    python docs/build_site.py site/
"""
from __future__ import annotations
import base64, json, os, sys, html as H
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path[:0] = [os.path.join(ROOT, "src"), os.path.join(ROOT, "tests")]
import compare                                        # renders the cases, writes tests/output
import plotlyhep as php
from plotlyhep.html import script_tag, embed, SLIDE_CSS
import plotly.graph_objects as go

out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "site")
os.makedirs(os.path.join(out, "img"), exist_ok=True)
metrics = compare.run()
def img(name):
    src = os.path.join(compare.OUT, name); dst = os.path.join(out, "img", name)
    open(dst, "wb").write(open(src, "rb").read()); return f"img/{name}"

DESC = {
 "axes_label": "empty axes with the CMS label (loc 0) and right/top-aligned axis titles",
 "step_hist": "two step histograms, data with error bars, legend — the everyday plot",
 "inside_label": "filled histogram, label inside the axes (loc 2)",
 "annotate_from_mpl": "matplotlib ax.annotate arrows, converted with from_mpl",
 "annotate_roundtrip": "the same, converted to Plotly and back to matplotlib",
 "convert_from_mpl": "the histogram figure built with mplhep, converted with from_mpl",
 "convert_roundtrip": "from_mpl then to_mpl: matplotlib → Plotly → matplotlib",
}
rows = []
for name, m in metrics.items():
    fig, p = compare.CASES[name]()
    if isinstance(p, go.Figure):
        p.update_layout(width=None, height=None, autosize=True)
        right = embed(p, f"fig-{name}", editable=True, inherit_template=False, height="520px")
    else:
        right = f'<img src="{img(name + "_plotly.png")}" alt="{name} candidate">'
    rows.append(f"""
<section class="case" id="{name}">
  <h2>{name}</h2><p class="desc">{H.escape(DESC.get(name, ""))}</p>
  <div class="triple">
    <figure><figcaption>mplhep (matplotlib) — ground truth</figcaption><img src="{img(name + '_mpl.png')}" alt="{name} mplhep"></figure>
    <figure><figcaption>plotlyhep — {"live: hover the bins, drag the annotations" if isinstance(p, go.Figure) else "matplotlib after the round trip"}</figcaption>{right}</figure>
    <figure><figcaption>difference (white = identical)</figcaption><img src="{img(name + '_diff.png')}" alt="{name} diff"></figure>
  </div>
  <p class="metrics">mean |Δ| = <b>{m['mean_abs_diff']:.2f}</b> grey levels · pixels differing by &gt; 40: <b>{100*m['frac_pixels_gt40']:.2f} %</b> · SSIM = <b>{m['ssim']:.3f}</b></p>
</section>""")

# a figure built WITHOUT plotlyhep, styled only by the page-level template
plain = go.Figure()
x = np.linspace(0, 200, 41); plain.add_trace(go.Bar(x=0.5 * (x[1:] + x[:-1]), y=np.exp(-((x[1:] - 90) / 30) ** 2) * 300, name="plain go.Bar"))
plain.update_layout(xaxis_title="m<sub>jj</sub> [GeV]", yaxis_title="Events", showlegend=True)
theme_demo = embed(plain, "fig-theme", editable=False, persist=False, height="480px")

page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><title>plotlyhep — mplhep, mirrored for Plotly</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
{script_tag("CMS", transparent=True)}
{SLIDE_CSS}
<style>
 body {{ margin: 0; font: 16px/1.5 -apple-system, "Segoe UI", Helvetica, Arial, sans-serif; color: #191c20; background: #fcfcfb; }}
 header {{ padding: 40px 6vw 24px; border-bottom: 1px solid rgba(0,0,0,.12); }}
 h1 {{ font-family: "TeX Gyre Heros", Helvetica, Arial, sans-serif; font-size: 40px; margin: 0 0 8px; }}
 h1 span {{ color: #1a4480; }} h2 {{ font-family: "IBM Plex Mono", Menlo, monospace; font-size: 18px; letter-spacing: .08em; text-transform: uppercase; color: #1a4480; margin: 0 0 4px; }}
 main {{ padding: 0 6vw 60px; }} section {{ padding: 32px 0; border-bottom: 1px solid rgba(0,0,0,.08); }}
 .triple {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 18px; }} @media (max-width: 1100px) {{ .triple {{ grid-template-columns: 1fr; }} }}
 figure {{ margin: 0; background: #fff; border: 1px solid rgba(0,0,0,.09); border-radius: 6px; padding: 8px; }} figcaption {{ font: 13px "IBM Plex Mono", Menlo, monospace; color: #5c636e; margin-bottom: 6px; }}
 figure img {{ width: 100%; height: auto; display: block; }} .desc {{ margin: 0 0 14px; color: #5c636e; }} .metrics {{ font: 14px "IBM Plex Mono", Menlo, monospace; color: #5c636e; margin: 12px 0 0; }}
 code {{ background: rgba(26,68,128,.07); padding: 1px 5px; border-radius: 3px; }} pre {{ background: #fff; border: 1px solid rgba(0,0,0,.09); border-radius: 6px; padding: 14px; overflow-x: auto; font-size: 14px; }}
 a {{ color: #1a4480; }}
</style></head><body>
<header><h1>plotlyhep <span>— mplhep, mirrored for Plotly</span></h1>
<p>The CMS / ATLAS look of <a href="https://github.com/scikit-hep/mplhep">mplhep</a>, for Plotly figures — plus <code>from_mpl</code> / <code>to_mpl</code> conversion of existing matplotlib figures. Fidelity is a <b>pixel diff</b> against mplhep, rendered on the same 1000 × 1000 grid, rerun on every commit. Hover the live figures: each bin answers with its range and content ± error. Drag an annotation: it stays where you put it.
<a href="https://github.com/DickyChant/plotlyhep">github.com/DickyChant/plotlyhep</a></p></header>
<main>
{''.join(rows)}
<section id="theme">
  <h2>one theme for the whole page</h2>
  <p class="desc">This figure is a plain <code>go.Bar</code> built without plotlyhep. It renders in the mplhep look because the page carries the template once — <code>script_tag("CMS")</code> publishes it as <code>window.PLOTLYHEP_TEMPLATE</code> and every embedded figure inherits it. That is the deck-level “CSS” for plots; real CSS covers only what sits around the figure (transparent ground, the deck's font).</p>
  <figure>{theme_demo}</figure>
<pre>from plotlyhep.html import script_tag, embed, SLIDE_CSS
head  += script_tag("CMS") + SLIDE_CSS          # once per deck
slide += embed(fig, "plot-s12", editable=True)   # per figure: hover, draggable annotations, edits persisted</pre>
</section>
</main></body></html>"""
open(os.path.join(out, "index.html"), "w").write(page)
open(os.path.join(out, "metrics.json"), "w").write(json.dumps(metrics, indent=1))
print("site:", os.path.join(out, "index.html"), f"({len(page)//1024} kB html, {len(os.listdir(os.path.join(out,'img')))} images)")
