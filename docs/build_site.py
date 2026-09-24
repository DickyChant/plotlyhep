"""Build the GitHub Pages gallery: real open-data physics, interactive.
    python docs/build_site.py site/
Reads docs/data/hzz4l.json (made once by docs/make_data.py); no network needed."""
from __future__ import annotations
import json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "src"))
import plotly.graph_objects as go
import plotlyhep as php
from plotlyhep.html import script_tag, embed, SLIDE_CSS
from plotlyhep._units import pt2px

out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "site"); os.makedirs(out, exist_ok=True)
D = json.load(open(os.path.join(HERE, "data", "hzz4l.json")))
E = np.asarray(D["edges"]); ctr = 0.5 * (E[1:] + E[:-1]); width = np.diff(E)
GROUP_ORDER = ["Z+jets, tt̄", "ZZ*", "Higgs"]                     # bottom -> top of the stack
GROUP_COLOR = {"Z+jets, tt̄": "#f89c20", "ZZ*": "#5790fc", "Higgs": "#e42536"}
CHANNEL_LABEL = {"all": "4e + 4μ + 2e2μ", "4e": "4e", "4mu": "4μ", "2e2mu": "2e2μ"}

def group_arrays(chan):
    """per group: yield, sumw2, raw, and the per-sample breakdown, for one channel (or all)."""
    g = {}
    for key, s in D["samples"].items():
        h = s if chan == "all" else s["by_channel"][chan]
        y, y2, n = np.asarray(h["yield"]), np.asarray(h["sumw2"]), np.asarray(h["raw"])
        G = g.setdefault(s["group"], {"y": np.zeros(len(ctr)), "y2": np.zeros(len(ctr)), "n": np.zeros(len(ctr), int), "parts": {}})
        G["y"] += y; G["y2"] += y2; G["n"] += n; G["parts"][key] = y
    return g

def hover_for(group, G, total):
    """One HTML string per bin: what the process is and what it contributes here."""
    rows = []
    for i in range(len(ctr)):
        share = 100 * G["y"][i] / total[i] if total[i] > 0 else 0
        parts = sorted(G["parts"].items(), key=lambda kv: -kv[1][i])
        lines = [f"<b>{group}</b> — {D['groups'][group]}",
                 f"m<sub>4ℓ</sub> ∈ [{E[i]:.2f}, {E[i+1]:.2f}) GeV",
                 f"expected <b>{G['y'][i]:.2f} ± {np.sqrt(G['y2'][i]):.2f}</b> events · {share:.0f} % of the stack · {G['n'][i]} raw MC events"]
        for key, arr in parts:
            s = D["samples"][key]
            if arr[i] > 0 or len(parts) == 1:
                lines.append(f"&nbsp;&nbsp;{key}: {arr[i]:.2f} — {s['description']}<br>&nbsp;&nbsp;&nbsp;&nbsp;{s['generator']}, σ = {s['xsec_pb']:.4g} pb, DSID {s['dsid']}")
        rows.append("<br>".join(lines))
    return rows

def build(chan, sig_scale=1.0):
    g = group_arrays(chan)
    total = sum(g[k]["y"] for k in GROUP_ORDER)
    data = np.asarray(D["data"]["counts"] if chan == "all" else D["data"]["by_channel"][chan], float)
    traces = []
    for grp in GROUP_ORDER:
        G = g[grp]; y = G["y"] * (sig_scale if grp == "Higgs" else 1.0)
        traces.append(go.Bar(x=ctr, y=y, width=width, name=grp + (f" × {sig_scale:g}" if grp == "Higgs" and sig_scale != 1 else ""),
                             marker=dict(color=GROUP_COLOR[grp], line=dict(width=0)), customdata=hover_for(grp, G, total),
                             hovertemplate="%{customdata}<extra></extra>", legendrank=GROUP_ORDER.index(grp)))
    # data: black points with Poisson bars; hover shows observed vs expected
    obs_hover = [f"<b>Data</b> ({', '.join('period ' + p for p in D['data']['periods'])}, {D['lumi_fb']:g} fb⁻¹)<br>m<sub>4ℓ</sub> ∈ [{E[i]:.2f}, {E[i+1]:.2f}) GeV<br>observed <b>{int(data[i])}</b> · expected {total[i]:.2f} (S = {g['Higgs']['y'][i]:.2f}, B = {total[i]-g['Higgs']['y'][i]:.2f})" for i in range(len(ctr))]
    traces.append(go.Scatter(x=ctr, y=data, mode="markers", name="Data", marker=dict(color="black", size=pt2px(4)),
                             error_y=dict(type="data", array=np.sqrt(data), thickness=pt2px(1), width=0, color="black"),
                             customdata=obs_hover, hovertemplate="%{customdata}<extra></extra>", legendrank=10))
    return traces

fig = php.figure("ATLAS", barmode="stack", bargap=0)
for t in build("all"): fig.add_trace(t)
php.set_xlabel(fig, "m<sub>4ℓ</sub> [GeV]"); php.set_ylabel(fig, "Events / 3.75 GeV", ticklabel_chars=2)
php.atlas.label(fig, "Open Data", data=True, lumi=D["lumi_fb"], com=13, loc=1)
fig.update_layout(showlegend=True, legend=dict(x=0.98, y=0.80, xanchor="right", yanchor="top", traceorder="reversed"),
                  hoverlabel=dict(bgcolor="white", font=dict(size=13, family="Helvetica, Arial"), align="left"),
                  hovermode="closest", yaxis=dict(rangemode="tozero"))
# --- controls: channel (rebuilds the traces), y scale, signal x10
chan_traces = {c: build(c) for c in ["all", "4e", "4mu", "2e2mu"]}
sig10 = build("all", 10.0)
def restyle(trs): return {"y": [t.y for t in trs], "customdata": [t.customdata for t in trs], "name": [t.name for t in trs]}
# controls live in the top margin, clear of the ATLAS label and the axes
fig.update_layout(margin=dict(l=118, r=30, t=100, b=84), updatemenus=[
    dict(type="dropdown", x=0.0, y=1.19, xanchor="left", yanchor="top", showactive=True, bgcolor="white", font=dict(size=13),
         buttons=[dict(label=f"channel: {CHANNEL_LABEL[c]}", method="restyle", args=[restyle(chan_traces[c])]) for c in ["all", "4e", "4mu", "2e2mu"]]),
    dict(type="buttons", direction="right", x=0.47, y=1.19, xanchor="left", yanchor="top", showactive=True, bgcolor="white", font=dict(size=13),
         buttons=[dict(label="linear", method="relayout", args=[{"yaxis.type": "linear"}]), dict(label="log", method="relayout", args=[{"yaxis.type": "log"}])]),
    dict(type="buttons", direction="right", x=0.68, y=1.19, xanchor="left", yanchor="top", showactive=True, bgcolor="white", font=dict(size=13),
         buttons=[dict(label="signal × 1", method="restyle", args=[restyle(chan_traces["all"])]), dict(label="signal × 10", method="restyle", args=[restyle(sig10)])]),
])
W, H = php.figsize_px("ATLAS")            # 800 x 600: the ATLAS figure size, embedded at native pixels
fig.update_layout(width=W, height=H)
hzz = embed(fig, "fig-hzz4l", editable=False, persist=False, inherit_template=False, width=f"{W}px", height=f"{H}px")


# ---------------------------------------------------------------- CMS dimuon spectrum
DM = json.load(open(os.path.join(HERE, "data", "dimuon.json")))
DE = np.asarray(DM["edges"]); dctr = np.sqrt(DE[1:] * DE[:-1]); dsets = list(DM["datasets"].keys())
def near_res(lo, hi):
    return [r["name"] for r in DM["resonances"] if lo <= r["mass"] < hi or abs(r["mass"] - np.sqrt(lo * hi)) < 0.02 * r["mass"]]
def dimuon_traces(key, sign):
    d = DM["datasets"][key]; y = np.asarray(d[sign], float)
    yy = np.where(y > 0, y, np.nan)                                     # log axis: empty bins break the line
    x = np.concatenate([DE[:1], DE, DE[-1:]]); ys = np.concatenate([[np.nan], yy, [yy[-1], np.nan]])
    hover = [f"m<sub>μμ</sub> ∈ [{DE[i]:.3f}, {DE[i+1]:.3f}) GeV<br><b>{int(y[i])}</b> {'opposite' if sign=='os' else 'same'}-sign pairs"
             + (f"<br>near the {', '.join(near_res(DE[i], DE[i+1]))}" if near_res(DE[i], DE[i+1]) else "") for i in range(len(dctr))]
    step = go.Scatter(x=x, y=ys, mode="lines", line=dict(shape="hv", width=pt2px(1.2), color="#1a4480" if sign == "os" else "#9c9ca1"),
                      name=f"{key} · {'opposite' if sign=='os' else 'same'}-sign", hoverinfo="skip", showlegend=True)
    carrier = go.Scatter(x=dctr, y=yy, mode="markers", marker=dict(size=8, opacity=0.02, color="#1a4480"), showlegend=False,
                         customdata=hover, hovertemplate="%{customdata}<extra></extra>")
    return step, carrier
key0 = "2012" if "2012" in dsets else dsets[0]
dfig = php.figure("CMS")
for t in dimuon_traces(key0, "os"): dfig.add_trace(t)
peak = lambda key, m: float(np.asarray(DM["datasets"][key]["os"])[np.searchsorted(DE, m) - 1] or 1)
for r in DM["resonances"]:
    ymax = peak(key0, r["mass"])
    if ymax < 2: continue                                              # label only peaks this dataset can show
    dfig.add_annotation(x=np.log10(r["mass"]), y=np.log10(max(ymax, 1)) + 0.18, xref="x", yref="y", text=r["name"], showarrow=True,
                        ax=0, ay=-34, arrowhead=0, arrowwidth=1, arrowcolor="#5c636e", font=dict(size=16, color="#191c20"),
                        hovertext=f"<b>{r['name']}</b> — m = {r['mass']:g} GeV, Γ = {r['width']}<br>{r['what']}" + (f"<br>{r['note']}" if r["note"] else ""),
                        hoverlabel=dict(bgcolor="white", font=dict(size=13)))
dfig.update_layout(width=900, height=600, margin=dict(l=112, r=30, t=100, b=84), showlegend=True,
                   legend=dict(x=0.98, y=0.98, xanchor="right", yanchor="top"), hovermode="closest",
                   hoverlabel=dict(bgcolor="white", font=dict(size=13, family="Helvetica, Arial"), align="left"),
                   xaxis=dict(type="log", range=[np.log10(0.25), np.log10(300)], tickvals=[0.3, 0.5, 1, 2, 3, 5, 10, 20, 30, 50, 100, 200],
                              ticktext=["0.3", "0.5", "1", "2", "3", "5", "10", "20", "30", "50", "100", "200"], minor=dict(ticks="")),
                   yaxis=dict(type="log", rangemode="normal"))
php.set_xlabel(dfig, "m<sub>μμ</sub> [GeV]"); php.set_ylabel(dfig, "Events / bin", ticklabel_chars=3)
php.cms.label(dfig, "Open Data", data=True, rlabel=f"{DM['datasets'][key0]['sqrt_s_TeV']} TeV", loc=0)
def dm_restyle(key, sign):
    a, b = dimuon_traces(key, sign); return {"y": [a.y, b.y], "customdata": [None, b.customdata], "name": [a.name, b.name], "line.color": [a.line.color, None]}
menus = [dict(type="buttons", direction="right", x=0.0, y=1.19, xanchor="left", yanchor="top", showactive=True, bgcolor="white", font=dict(size=13),
              buttons=[dict(label="opposite-sign", method="restyle", args=[dm_restyle(key0, "os")]), dict(label="same-sign", method="restyle", args=[dm_restyle(key0, "ss")])]),
         dict(type="buttons", direction="right", x=0.36, y=1.19, xanchor="left", yanchor="top", showactive=True, bgcolor="white", font=dict(size=13),
              buttons=[dict(label="full", method="relayout", args=[{"xaxis.range": [np.log10(0.25), np.log10(300)]}]),
                       dict(label="J/ψ", method="relayout", args=[{"xaxis.range": [np.log10(2.6), np.log10(4.4)]}]),
                       dict(label="Υ", method="relayout", args=[{"xaxis.range": [np.log10(8.6), np.log10(11.4)]}]),
                       dict(label="Z", method="relayout", args=[{"xaxis.range": [np.log10(60), np.log10(130)]}])])]
if len(dsets) > 1:
    menus.append(dict(type="dropdown", x=0.76, y=1.19, xanchor="left", yanchor="top", showactive=True, bgcolor="white", font=dict(size=13),
                      buttons=[dict(label=f"{k}: {DM['datasets'][k]['n_events']/1e6:.1f} M events" if DM['datasets'][k]['n_events'] > 1e6 else f"{k}: {DM['datasets'][k]['n_events']//1000}k events",
                                    method="restyle", args=[dm_restyle(k, "os")]) for k in sorted(dsets, reverse=True)]))
dfig.update_layout(updatemenus=menus)
dimuon = embed(dfig, "fig-dimuon", editable=False, persist=False, inherit_template=False, width="900px", height="600px")
dm_desc = " · ".join(f"{k}: {DM['datasets'][k]['description']}" for k in sorted(dsets, reverse=True))

n_sel = {k: s["selected_raw"] for k, s in D["samples"].items()}
page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><title>plotlyhep — gallery</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
{script_tag(None)}
{SLIDE_CSS}
<style>
 body {{ margin: 0; font: 16px/1.55 -apple-system, "Segoe UI", Helvetica, Arial, sans-serif; color: #191c20; background: #fcfcfb; }}
 header {{ padding: 40px 6vw 22px; border-bottom: 1px solid rgba(0,0,0,.12); }}
 h1 {{ font-family: "TeX Gyre Heros", Helvetica, Arial, sans-serif; font-size: 40px; margin: 0 0 8px; }} h1 span {{ color: #1a4480; }}
 h2 {{ font-family: "IBM Plex Mono", Menlo, monospace; font-size: 17px; letter-spacing: .08em; text-transform: uppercase; color: #1a4480; margin: 0 0 6px; }}
 main {{ padding: 0 6vw 60px; max-width: 1200px; }} section {{ padding: 34px 0; border-bottom: 1px solid rgba(0,0,0,.08); }}
 .fig {{ background: #fff; border: 1px solid rgba(0,0,0,.09); border-radius: 6px; padding: 10px; display: inline-block; max-width: 100%; overflow-x: auto; }}
 .try {{ font: 14px "IBM Plex Mono", Menlo, monospace; color: #5c636e; margin: 10px 0 0; }}
 code {{ background: rgba(26,68,128,.07); padding: 1px 5px; border-radius: 3px; }} pre {{ background: #fff; border: 1px solid rgba(0,0,0,.09); border-radius: 6px; padding: 14px; overflow-x: auto; font-size: 14px; }}
 a {{ color: #1a4480; }} .small {{ color: #5c636e; font-size: 14px; }}
</style></head><body>
<header><h1>plotlyhep <span>— gallery</span></h1>
<p>The mplhep look for Plotly, on real open data. Every element of a plot knows what it is: hover a stacked process and it tells you which samples it is made of, how they were generated, their cross sections and what they contribute in that bin. <a href="https://github.com/DickyChant/plotlyhep">github.com/DickyChant/plotlyhep</a></p></header>
<main>
<section id="hzz4l">
  <h2>H → ZZ* → 4ℓ — ATLAS Open Data, 13 TeV, {D['lumi_fb']:g} fb⁻¹</h2>
  <p>The four-lepton invariant mass after the standard selection ({D['selection']}), Higgs signal stacked on the ZZ* and reducible backgrounds, data with Poisson errors. Built from <a href="https://opendata.cern.ch/record/15005">CERN Open Data record 15005</a> with the normalisation of the ATLAS outreach framework; the same selection as ROOT's <code>df106_HiggsToFourLeptons</code> tutorial.</p>
  <div class="fig">{hzz}</div>
  <p class="try">try: hover a stack segment · hover a data point (observed vs S and B) · click a legend entry to hide it, double-click to isolate it · channel dropdown · log axis · signal × 10 · drag to zoom, double-click to reset</p>
  <p class="small">Selected events: data {D['data']['selected']} · MC after selection: {', '.join(f'{k} {v}' for k, v in n_sel.items())}. Reduced once by <code>docs/make_data.py</code> to a {os.path.getsize(os.path.join(HERE,'data','hzz4l.json'))//1024} kB JSON; this page is built from that file alone.</p>
</section>
<section id="dimuon">
  <h2>the dimuon spectrum — CMS Open Data</h2>
  <p>Every opposite-sign muon pair's invariant mass on a log–log axis: three decades of QCD and electroweak physics in one histogram, from the light mesons through the charmonium and bottomonium families to the Z. Hover a peak's label to learn what it is; hover a bin for its count; zoom to a family. {dm_desc}.</p>
  <div class="fig">{dimuon}</div>
  <p class="try">try: hover the J/ψ or Υ labels · opposite- vs same-sign (no resonances in same-sign pairs: the peaks are physics, not detector artefacts) · zoom presets · drag a region · double-click to reset</p>
</section>
<section id="use">
  <h2>use it</h2>
<pre>import plotlyhep as php
fig = php.figure("ATLAS", barmode="stack", bargap=0)
fig.add_trace(go.Bar(x=centres, y=yields, width=widths, name="ZZ*", customdata=per_bin_html, hovertemplate="%{{customdata}}&lt;extra&gt;&lt;/extra&gt;"))
php.atlas.label(fig, "Open Data", data=True, lumi=10, com=13, loc=1)
php.set_xlabel(fig, "m&lt;sub&gt;4ℓ&lt;/sub&gt; [GeV]"); php.set_ylabel(fig, "Events / 3.75 GeV")

# in an HTML deck: once per page, then per figure
head  += php.html.script_tag("ATLAS") + php.html.SLIDE_CSS
slide += php.html.embed(fig, "plot-s12", editable=True)      # hover, draggable annotations, edits persisted</pre>
  <p class="small">Fidelity to mplhep is measured, not asserted: every commit renders the same figures through mplhep and plotlyhep on a 1000 × 1000 grid and diffs the pixels — see the <a href="https://github.com/DickyChant/plotlyhep/actions">pixel-diff workflow</a> and the README table.</p>
</section>
</main></body></html>"""
open(os.path.join(out, "index.html"), "w").write(page)
print("site:", os.path.join(out, "index.html"), f"({len(page)//1024} kB)")
