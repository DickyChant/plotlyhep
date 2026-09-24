"""The two ROOT-tutorial plots, rebuilt in Plotly to be pixel-comparable with the tutorial output:
   df102_NanoAODDimuonAnalysis  (CMS Open Data dimuon spectrum, canvas 800x700)
   df106_HiggsToFourLeptons     (ATLAS Open Data H->ZZ*->4l, canvas 600x600, ATLAS style)
Geometry, sizes and positions follow the tutorial sources; colours were sampled from the
reference images. Hover carries the physics on top."""

from __future__ import annotations

import json
import os

import numpy as np
import plotly.graph_objects as go

import plotlyhep as php
from plotlyhep.styles import ROOT_EM

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
DESC = 0.22  # Plotly anchors 'bottom' at the text box bottom; ROOT's bottom is the baseline (descender ≈ 0.22 em)


def ndc(margins):
    """ROOT NDC (canvas fractions) -> Plotly paper fractions (plot area inside the margins)."""
    l, r, t, b = margins
    return (lambda x: (x - l) / (1 - l - r)), (lambda y: (y - b) / (1 - t - b))


# ------------------------------------------------------------------ df102
def dimuon_df102(DM: dict | None = None, scale: float = 3.0) -> go.Figure:
    """scale: the raster scale the figure will be rendered at; ROOT keeps line widths in device
    pixels while text scales with the canvas, so 1-px ROOT lines are 1/scale here."""
    DM = DM or json.load(open(os.path.join(DATA, "dimuon.json")))
    W, H = 796, 672  # the tutorial's 800x700 canvas as ROOT saves it
    lw = 1.0 / scale
    d = DM["datasets"]["2012_root"]
    lo, hi, n = DM["root_edges"]
    E = np.linspace(lo, hi, n + 1)
    y = np.asarray(d["os"], float)
    fig = go.Figure(layout=dict(template=php.root_template(W, H, label_size=0.035, title_size=0.04, tick_len=0.03, frame_width=lw)))
    # ROOT's painter collapses bins sharing a device pixel column into one vertical min-max stroke,
    # and draws empty bins at the axis minimum on a log scale: that is what makes the high-mass "grass".
    YMIN, YMAX = 0.5, 4.9e5
    ncol = int(0.8 * W * scale)  # device pixel columns across the plot area
    lx0, lx1 = np.log10(0.25), np.log10(300)
    col = np.floor((np.log10(0.5 * (E[1:] + E[:-1])) - lx0) / (lx1 - lx0) * ncol).astype(int)
    yv = np.where(y > 0, y, YMIN)
    lo = np.full(ncol, np.inf)
    hi = np.full(ncol, -np.inf)
    np.minimum.at(lo, col, yv)
    np.maximum.at(hi, col, yv)
    used = np.isfinite(lo)
    xs = 10 ** (lx0 + (np.arange(ncol)[used] + 0.5) / ncol * (lx1 - lx0))
    path_x = np.repeat(xs, 2)
    path_y = np.column_stack([lo[used], hi[used]]).ravel()
    fig.add_trace(
        go.Scatter(
            x=path_x, y=path_y, mode="lines", line=dict(width=lw, color="#000099"), hoverinfo="skip", showlegend=False, name="Dimuon_mass"
        )
    )
    # hover from the log-binned reduction: one carrier per bin, invisible
    LE = np.asarray(DM["edges"])
    ctr = np.sqrt(LE[1:] * LE[:-1])
    yl = np.asarray(DM["datasets"]["2012"]["os"], float)
    res = DM["resonances"]
    near = lambda a, b: [r["name"] for r in res if a <= r["mass"] < b or abs(r["mass"] - np.sqrt(a * b)) < 0.02 * r["mass"]]
    hov = [
        f"m<sub>μμ</sub> ∈ [{LE[i]:.3f}, {LE[i + 1]:.3f}) GeV<br><b>{int(yl[i])}</b> opposite-sign pairs"
        + (f"<br>near the {', '.join(near(LE[i], LE[i + 1]))}" if near(LE[i], LE[i + 1]) else "")
        for i in range(len(ctr))
    ]
    idx = np.clip(np.searchsorted(E, ctr) - 1, 0, len(y) - 1)
    yc = np.where(y[idx] > 0, y[idx], np.nan)  # sit on the drawn line
    fig.add_trace(
        go.Scatter(
            x=ctr,
            y=yc,
            mode="markers",
            marker=dict(size=8, color="rgba(0,0,0,0)"),
            showlegend=False,
            customdata=hov,
            hovertemplate="%{customdata}<extra></extra>",
        )
    )
    lab = dict(xref="paper", yref="paper", xanchor="left", yanchor="bottom", showarrow=False)
    px = lambda f: ROOT_EM * f * H  # ROOT text sizes: fractions of the pad height, em = 0.90 x
    X, Y = ndc((0.10, 0.10, 0.10, 0.10))
    for name, x, yv in (
        ("η", 0.175, 0.740),
        ("ρ,ω", 0.205, 0.775),
        ("φ", 0.270, 0.740),
        ("J/ψ", 0.400, 0.800),
        ("ψ'", 0.415, 0.670),
        ("Y(1,2,3S)", 0.485, 0.700),
        ("Z", 0.755, 0.680),
    ):
        r = [
            q
            for q in res
            if q["name"].split("(")[0].replace(" / ", ",").startswith(name.split("(")[0].replace("Y", "Υ").replace("ψ'", "ψ(2S"))
        ]
        text = (
            "<br>".join(
                f"<b>{q['name']}</b> — m = {q['mass']:g} GeV, Γ = {q['width']}<br>{q['what']}" + (f"<br>{q['note']}" if q["note"] else "")
                for q in r
            )
            or name
        )
        fig.add_annotation(
            text=name,
            x=X(x),
            y=Y(yv),
            yshift=-DESC * px(0.05),
            font=dict(size=px(0.05)),
            hovertext=text,
            hoverlabel=dict(bgcolor="white", font=dict(size=13)),
            **lab,
        )
    fig.add_annotation(text="<b>CMS Open Data</b>", x=X(0.100), y=Y(0.920), yshift=-DESC * px(0.04), font=dict(size=px(0.040)), **lab)
    fig.add_annotation(
        text="√s = 8 TeV, L<sub>int</sub> = 11.6 fb<sup>-1</sup>",
        x=X(0.630),
        y=Y(0.920),
        yshift=-DESC * px(0.03),
        font=dict(size=px(0.030)),
        **lab,
    )
    fig.update_layout(
        # explicit ROOT-style labels: Plotly's exponentformat="power" renders its labels ~25 % larger
        xaxis=dict(
            type="log",
            range=[np.log10(0.25), np.log10(300)],
            tickmode="array",
            tickvals=[1, 10, 100],
            ticktext=["1", "10", "10<sup>2</sup>"],
            minor=dict(dtick="D1", ticks="inside", ticklen=0.015 * 0.8 * H, tickwidth=lw),
        ),
        yaxis=dict(
            type="log",
            range=[np.log10(YMIN), np.log10(YMAX)],
            tickmode="array",
            tickvals=[10.0**k for k in range(6)],
            ticktext=["1", "10"] + [f"10<sup>{k}</sup>" for k in range(2, 6)],
            minor=dict(dtick="D1", ticks="inside", ticklen=0.015 * 0.8 * W, tickwidth=lw),
        ),
        hoverlabel=dict(bgcolor="white", font=dict(size=13, family="Helvetica, Arial"), align="left"),
    )
    # axis titles at the axis ends, ROOT style (title offset 1)
    # measured on the reference: x title top 11 px below the frame; y title right edge 33 px left of it, top-aligned
    fig.add_annotation(
        text="m<sub>μμ</sub> (GeV)",
        xref="paper",
        yref="paper",
        x=1,
        y=0,
        xanchor="right",
        yanchor="top",
        yshift=-8,
        font=dict(size=px(0.04)),
        showarrow=False,
    )
    fig.add_annotation(
        text="N<sub>Events</sub>",
        xref="paper",
        yref="paper",
        x=0,
        y=1,
        xanchor="center",
        yanchor="top",
        textangle=-90,
        xshift=-(33 + 0.6 * px(0.04)),
        font=dict(size=px(0.04)),
        showarrow=False,
    )
    return fig


# ------------------------------------------------------------------ df106
def hzz_df106(D: dict | None = None) -> go.Figure:
    D = D or json.load(open(os.path.join(DATA, "hzz4l_root.json")))
    W, H = 596, 572  # the tutorial's 600x600 canvas as ROOT saves it
    E = np.asarray(D["edges"])
    ctr = 0.5 * (E[1:] + E[:-1])
    n = len(ctr)
    fig = go.Figure(
        layout=dict(
            template=php.root_template(
                W, H, label_size=0.04, title_size=0.045, margins=(0.16, 0.05, 0.05, 0.16), tick_len=0.02, frame_width=1
            )
        )
    )
    cat = {k: np.asarray(v, float) for k, v in D["categories"].items()}
    other, zz, higgs = cat["other"], cat["zz"], cat["higgs"]
    tot = D["mc_total"]
    nom, up, dn = (np.asarray(tot[k], float) for k in ("nominal", "up", "down"))
    err = up - nom

    def step(yv):  # stairs with edges down to zero, like HIST
        return np.concatenate([[E[0]], E, [E[-1]]]), np.concatenate([[0.0], yv, [yv[-1], 0.0]])

    COL = {"higgs": "#990000", "zz": "#99ccff", "other": "#cc99ff"}
    S = D["samples"]

    def hover(cname, yv):
        parts = [(k, s) for k, s in S.items() if s["category"] == cname]
        rows = []
        for i in range(n):
            lines = [
                f"<b>{ {'higgs': 'Higgs MC', 'zz': 'ZZ MC', 'other': 'Other MC'}[cname] }</b> · m<sub>4ℓ</sub> ∈ [{E[i]:.2f}, {E[i + 1]:.2f}) GeV",
                f"expected <b>{yv[i]:.2f}</b> events · {100 * yv[i] / nom[i] if nom[i] > 0 else 0:.0f} % of the stack",
            ]
            for k, s in parts:
                if s["yield"][i] > 0:
                    lines.append(
                        f"&nbsp;&nbsp;{k}: {s['yield'][i]:.2f} — {s['description']}<br>&nbsp;&nbsp;&nbsp;&nbsp;{s['generator']}, σ = {s['xsec_pb']:.4g} pb"
                        + (f", × {s['scale']}" if s["scale"] != 1 else "")
                    )
            rows.append("<br>".join(lines))
        return rows

    # stacked filled steps, drawn total-first so each lower layer paints over the one above
    for cname, top in (("higgs", other + zz + higgs), ("zz", other + zz), ("other", other)):
        x, yv = step(top)
        fig.add_trace(
            go.Scatter(
                x=x,
                y=yv,
                mode="lines",
                fill="tozeroy",
                fillcolor=COL[cname],
                line=dict(shape="hv", width=1, color="black"),
                hoverinfo="skip",
                showlegend=False,
                name=cname,
            )
        )
    for cname, top, own in (("other", other, other), ("zz", other + zz, zz), ("higgs", other + zz + higgs, higgs)):
        fig.add_trace(
            go.Scatter(
                x=ctr,
                y=top - own / 2,
                mode="markers",
                marker=dict(size=10, opacity=0.02, color=COL[cname]),
                showlegend=False,
                customdata=hover(cname, own),
                hovertemplate="%{customdata}<extra></extra>",
            )
        )
    # total MC uncertainty band (E2, hatched 3254) and the up/down variations (HIST)
    xl, lo_y = step(nom - err)
    _, hi_y = step(nom + err)
    fig.add_trace(
        go.Scatter(x=xl, y=lo_y, mode="lines", line=dict(shape="hv", width=0.5, color="black"), hoverinfo="skip", showlegend=False)
    )
    fig.add_trace(
        go.Scatter(
            x=xl,
            y=hi_y,
            mode="lines",
            line=dict(shape="hv", width=0.5, color="black"),
            fill="tonexty",
            fillpattern=dict(shape="/", fgcolor="black", bgcolor="rgba(0,0,0,0)", size=5, solidity=0.35),
            hoverinfo="skip",
            showlegend=False,
        )
    )
    bh = [
        f"<b>Total MC</b> · [{E[i]:.2f}, {E[i + 1]:.2f}) GeV<br>nominal {nom[i]:.2f} · variation up {up[i]:.2f} / down {dn[i]:.2f}<br>electron scale-factor uncertainty band ± {err[i]:.2f}"
        for i in range(n)
    ]
    fig.add_trace(
        go.Scatter(
            x=ctr,
            y=nom,
            mode="markers",
            marker=dict(size=6, opacity=0.02),
            showlegend=False,
            customdata=bh,
            hovertemplate="%{customdata}<extra></extra>",
        )
    )
    for yv, col in ((up, "#009900"), (dn, "#000099")):
        x, s_ = step(yv)
        fig.add_trace(go.Scatter(x=x, y=s_, mode="lines", line=dict(shape="hv", width=1, color=col), hoverinfo="skip", showlegend=False))
    # data: marker style 20 size 1.2, error bars width 2 with small caps; empty bins not drawn (option E)
    data = np.asarray(D["data"]["counts"], float)
    m = data > 0
    dh = [
        f"<b>Data</b> · [{E[i]:.2f}, {E[i + 1]:.2f}) GeV<br>observed <b>{int(data[i])}</b> · expected {nom[i]:.2f} (S = {higgs[i]:.2f}, B = {nom[i] - higgs[i]:.2f})"
        for i in range(n)
    ]
    fig.add_trace(
        go.Scatter(
            x=ctr[m],
            y=data[m],
            mode="markers",
            marker=dict(symbol="circle", size=9.5, color="black"),
            error_y=dict(type="data", array=np.sqrt(data[m]), thickness=2, width=0, color="black"),  # no caps (option E)
            error_x=dict(
                type="constant", value=0.5 * (E[1] - E[0]), thickness=2, width=0, color="black"
            ),  # gStyle ErrorX = 0.5: bar across the bin
            customdata=[dh[i] for i in range(n) if m[i]],
            hovertemplate="%{customdata}<extra></extra>",
            showlegend=False,
            name="Data",
        )
    )
    # axes
    fig.update_layout(
        xaxis=dict(range=[80, 170], dtick=10, minor=dict(dtick=2, ticks="inside", ticklen=0.01 * H)),
        yaxis=dict(
            range=[0, 35],
            tickvals=list(range(0, 36, 5)),
            ticktext=[""] + [str(v) for v in range(5, 36, 5)],
            minor=dict(dtick=1, ticks="inside", ticklen=0.01 * W),
        ),
        hoverlabel=dict(bgcolor="white", font=dict(size=13, family="Helvetica, Arial"), align="left"),
    )
    px = lambda f: ROOT_EM * f * H
    X, Y = ndc((0.16, 0.05, 0.05, 0.16))
    # measured on the reference: x title top 41 px below the frame; y title right edge 51 px left of it, top-aligned
    fig.add_annotation(
        text="m<sub>4l</sub><sup>H→ ZZ</sup> [GeV]",
        xref="paper",
        yref="paper",
        x=1,
        y=0,
        xanchor="right",
        yanchor="top",
        yshift=-38,
        font=dict(size=px(0.045)),
        showarrow=False,
    )
    fig.add_annotation(
        text="Events",
        xref="paper",
        yref="paper",
        x=0,
        y=1,
        xanchor="center",
        yanchor="top",
        textangle=-90,
        xshift=-(51 + 0.6 * px(0.045)),
        font=dict(size=px(0.045)),
        showarrow=False,
    )
    lab = dict(xref="paper", yref="paper", xanchor="left", yanchor="bottom", showarrow=False)
    fig.add_annotation(text="<b><i>ATLAS</i></b>", x=X(0.19), y=Y(0.85), yshift=-DESC * px(0.04), font=dict(size=px(0.04)), **lab)
    fig.add_annotation(text="Open Data", x=X(0.34), y=Y(0.85), yshift=-DESC * px(0.04), font=dict(size=px(0.04)), **lab)
    fig.add_annotation(
        text="√s = 13 TeV, 10 fb<sup>-1</sup>", x=X(0.21), y=Y(0.80), yshift=-DESC * px(0.035), font=dict(size=px(0.035)), **lab
    )
    # legend, drawn by hand: TLegend(0.57, 0.65, 0.94, 0.94), text 0.025, right-aligned, symbol column 25 %
    x0, x1, y0, y1 = X(0.57), X(0.94), Y(0.65), Y(0.94)
    rows = 7
    rh = (y1 - y0) / rows
    sx0, sx1 = x0 + (X(0.59) - X(0.57)), x0 + 0.25 * (x1 - x0) - (X(0.58) - X(0.57))
    entries = [
        ("Data", "lep"),
        ("Higgs MC", COL["higgs"]),
        ("ZZ MC", COL["zz"]),
        ("Other MC", COL["other"]),
        ("Total MC Variations Down", "#000099"),
        ("Total MC Variations Up", "#009900"),
        ("Total MC Uncertainty", "hatch"),
    ]
    for k, (text, sym) in enumerate(entries):
        yc = y1 - (k + 0.5) * rh
        fig.add_annotation(
            text=text,
            x=x1 - (X(0.58) - X(0.57)),
            y=yc,
            xref="paper",
            yref="paper",
            xanchor="right",
            yanchor="middle",
            showarrow=False,
            font=dict(size=px(0.025)),
        )
        if sym == "lep":
            xm = (sx0 + sx1) / 2
            fig.add_shape(
                type="line",
                xref="paper",
                yref="paper",
                x0=xm,
                x1=xm,
                y0=yc - rh * 0.45,
                y1=yc + rh * 0.45,
                line=dict(color="black", width=2),
            )
            fig.add_shape(type="line", xref="paper", yref="paper", x0=sx0, x1=sx1, y0=yc, y1=yc, line=dict(color="black", width=2))
            fig.add_shape(
                type="circle",
                xref="paper",
                yref="paper",
                x0=xm - 4.75 / W,
                x1=xm + 4.75 / W,
                y0=yc - 4.75 / H,
                y1=yc + 4.75 / H,
                line=dict(color="black", width=1),
                fillcolor="black",
            )
        elif sym == "hatch":
            fig.add_shape(
                type="rect",
                xref="paper",
                yref="paper",
                x0=sx0,
                x1=sx1,
                y0=yc - rh * 0.35,
                y1=yc + rh * 0.35,
                line=dict(color="black", width=0.5),
                fillcolor="rgba(0,0,0,0)",
            )
            bw = (sx1 - sx0) * W
            bh = rh * 0.7 * H  # hatch: 45° lines every 5 px, clipped to the box
            for k in range(-int(bh), int(bw), 5):
                xa, ya = k, 0.0
                xb, yb = k + bh, bh
                xa2, xb2 = max(xa, 0), min(xb, bw)
                ya2 = ya + (xa2 - xa)
                yb2 = yb - (xb - xb2)
                if xb2 > xa2:
                    fig.add_shape(
                        type="line",
                        xref="paper",
                        yref="paper",
                        x0=sx0 + xa2 / W,
                        x1=sx0 + xb2 / W,
                        y0=yc - rh * 0.35 + ya2 / H,
                        y1=yc - rh * 0.35 + yb2 / H,
                        line=dict(color="black", width=0.6),
                    )
        elif sym.startswith("#") and text.endswith("MC"):
            fig.add_shape(
                type="rect",
                xref="paper",
                yref="paper",
                x0=sx0,
                x1=sx1,
                y0=yc - rh * 0.35,
                y1=yc + rh * 0.35,
                line=dict(color="black", width=1),
                fillcolor=sym,
            )
        else:
            fig.add_shape(type="line", xref="paper", yref="paper", x0=sx0, x1=sx1, y0=yc, y1=yc, line=dict(color=sym, width=1))
    return fig
