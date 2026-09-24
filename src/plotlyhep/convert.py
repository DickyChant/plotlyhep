"""Figure conversion in both directions.

from_mpl(fig)  — walk a *drawn* matplotlib figure and rebuild it as a Plotly figure,
                 geometry-faithfully: every artist becomes the trace/annotation that draws
                 the same pixels (text is placed by its rendered window extent, tick labels
                 are copied verbatim, error bars become their segments).
to_mpl(fig)    — the reverse for the common Plotly trace types.

Both are checked by the pixel-diff harness in tests/ against the original render."""
from __future__ import annotations
import re
import numpy as np
import plotly.graph_objects as go
from ._units import pt2px

# ----------------------------------------------------------------- text helpers
def mathtext_to_html(s: str) -> str:
    """Crude but useful: $m_{jj}$ -> m<sub>jj</sub>, $x^{2}$ -> x<sup>2</sup>."""
    def conv(m):
        t = m.group(1)
        t = re.sub(r"\\mathrm\{([^}]*)\}", r"\1", t)
        t = re.sub(r"\\text\{([^}]*)\}", r"\1", t)
        t = re.sub(r"_\{([^}]*)\}", r"<sub>\1</sub>", t)
        t = re.sub(r"\^\{([^}]*)\}", r"<sup>\1</sup>", t)
        t = re.sub(r"_(\w)", r"<sub>\1</sub>", t)
        t = re.sub(r"\^(\w)", r"<sup>\1</sup>", t)
        t = t.replace(r"\,", " ").replace(r"\;", " ").replace(r"\ ", " ")
        return t
    return re.sub(r"\$([^$]*)\$", conv, s)

def html_to_mathtext(s: str) -> str:
    s = re.sub(r"<sub>([^<]*)</sub>", r"$_{\1}$", s)
    s = re.sub(r"<sup>([^<]*)</sup>", r"$^{\1}$", s)
    s = re.sub(r"</?[bi]>", "", s)
    return s.replace("$$", "")

def _rgba(c, alpha=None) -> str:
    import matplotlib.colors as mc
    r, g, b, a = mc.to_rgba(c)
    if alpha is not None: a = alpha
    return f"rgba({int(r*255)},{int(g*255)},{int(b*255)},{a:.3f})"

_DASH = {"-": "solid", "--": "dash", "-.": "dashdot", ":": "dot", "solid": "solid", "dashed": "dash",
         "dashdot": "dashdot", "dotted": "dot"}
_MARK = {"o": "circle", ".": "circle", "s": "square", "^": "triangle-up", "v": "triangle-down",
         "D": "diamond", "d": "diamond", "x": "x", "+": "cross", "*": "star", "None": None, "none": None, "": None}

# ----------------------------------------------------------------- from_mpl
def from_mpl(fig, *, dpi: float | None = None) -> go.Figure:
    import matplotlib
    from matplotlib.lines import Line2D
    from matplotlib.patches import StepPatch, Rectangle, Polygon
    from matplotlib.collections import PathCollection, PolyCollection, LineCollection, QuadMesh
    from matplotlib.image import AxesImage
    dpi = dpi or fig.dpi
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    W, H = fig.get_size_inches() * dpi
    px = lambda pt: float(pt) * dpi / 72.0
    rc = matplotlib.rcParams
    fam = ", ".join(rc["font.sans-serif"]) if rc["font.family"] == ["sans-serif"] or rc["font.family"] == "sans-serif" else ", ".join(rc["font.family"])
    out = go.Figure()
    layout = dict(width=int(round(W)), height=int(round(H)), paper_bgcolor="white", plot_bgcolor="white",
                  margin=dict(l=0, r=0, t=0, b=0, pad=0), showlegend=False,
                  font=dict(family=fam, size=px(rc["font.size"]), color="black"))
    axes = [a for a in fig.get_axes() if a.get_label() != "<colorbar>"]
    def to_paper(bbox):   # display bbox -> paper fractions
        return bbox.x0 / W, bbox.x1 / W, bbox.y0 / H, bbox.y1 / H
    for k, ax in enumerate(axes):
        xs = "x" if k == 0 else f"x{k+1}"; ys = "y" if k == 0 else f"y{k+1}"
        xkey = "xaxis" if k == 0 else f"xaxis{k+1}"; ykey = "yaxis" if k == 0 else f"yaxis{k+1}"
        x0, x1, y0, y1 = to_paper(ax.get_window_extent(renderer))
        def axis_dict(axis, lo, hi, dom, spine_lw):
            ticks = axis.get_majorticklocs(); ticks = ticks[(ticks >= min(lo, hi)) & (ticks <= max(lo, hi))]
            labels = [t.get_text() for t in axis.get_majorticklabels()]
            # matplotlib keeps labels for all locs; align by position
            alllocs = list(axis.get_majorticklocs()); ticktext = []
            for t in ticks:
                i = alllocs.index(t); ticktext.append(mathtext_to_html(labels[i]) if i < len(labels) else str(t))
            mt = axis.get_minorticklocs(); mt = mt[(mt >= min(lo, hi)) & (mt <= max(lo, hi))]
            t1 = axis.get_major_ticks()[0] if axis.get_major_ticks() else None
            tlen = px(t1.tick1line.get_markersize()) if t1 else px(3.5)
            tw = px(t1.tick1line.get_markeredgewidth()) if t1 else px(0.8)
            tdir = rc[f"{axis.axis_name}tick.direction"]
            m1 = axis.get_minor_ticks()[0] if len(mt) and axis.get_minor_ticks() else None
            tfs = px(axis.get_majorticklabels()[0].get_fontsize()) if labels else px(rc["font.size"])
            both = axis.get_ticks_position() == "default" and (rc[f"{axis.axis_name}tick.top" if axis.axis_name == "x" else "ytick.right"])
            d = dict(range=[lo, hi], domain=dom, showline=True, linecolor="black", linewidth=spine_lw,
                     mirror="allticks" if both else True, ticks="inside" if tdir == "in" else "outside",
                     ticklen=tlen, tickwidth=tw, tickcolor="black", tickmode="array", tickvals=list(ticks),
                     ticktext=ticktext, tickfont=dict(size=tfs), showgrid=False, zeroline=False, automargin=False,
                     type="log" if axis.get_scale() == "log" else "linear", anchor=ys if axis.axis_name == "x" else xs)
            if axis.get_scale() == "log": d["range"] = [np.log10(lo), np.log10(hi)]
            if len(mt):
                d["minor"] = dict(ticks=d["ticks"], ticklen=px(m1.tick1line.get_markersize()) if m1 else tlen / 2,
                                  tickwidth=px(m1.tick1line.get_markeredgewidth()) if m1 else tw, tickvals=list(mt), showgrid=False)
            return d
        lw = px(ax.spines["left"].get_linewidth())
        layout[xkey] = axis_dict(ax.xaxis, *ax.get_xlim(), [x0, x1], lw)
        layout[ykey] = axis_dict(ax.yaxis, *ax.get_ylim(), [y0, y1], lw)
        # ---- artists
        for ln in ax.lines:
            x, y = ln.get_xdata(), ln.get_ydata()
            if len(x) == 0: continue
            ds = ln.get_drawstyle(); shape = {"steps-post": "hv", "steps-pre": "vh", "steps-mid": "hvh", "steps": "vh"}.get(ds, "linear")
            ls = _DASH.get(ln.get_linestyle(), "solid"); mk = _MARK.get(str(ln.get_marker()), None)
            has_line = ln.get_linestyle() not in ("None", "none", "", " ")
            mode = "+".join([m for m, ok in (("lines", has_line), ("markers", mk is not None)) if ok]) or "lines"
            col = _rgba(ln.get_color(), ln.get_alpha())
            lab = ln.get_label(); show = not str(lab).startswith("_")
            out.add_trace(go.Scatter(x=x, y=y, mode=mode, name=lab if show else "", showlegend=show, xaxis=xs, yaxis=ys,
                                     line=dict(shape=shape, width=px(ln.get_linewidth()), dash=ls, color=col),
                                     marker=dict(symbol=mk or "circle", size=px(ln.get_markersize()) * (0.5 if ln.get_marker() == "." else 1.0),
                                                 color=_rgba(ln.get_markerfacecolor(), ln.get_alpha()) if ln.get_markerfacecolor() != "none" else "rgba(0,0,0,0)",
                                                 line=dict(color=_rgba(ln.get_markeredgecolor()), width=px(ln.get_markeredgewidth())))))
        bars_x, bars_y, bars_w, bars_c = [], [], [], []
        for p in ax.patches:
            if isinstance(p, StepPatch):
                v, e = p.get_data()[0], p.get_data()[1]
                base = p.get_data()[2] if len(p.get_data()) > 2 else None
                xx = np.concatenate([[e[0]], e, [e[-1]]]) if base is not None else e
                yy = np.concatenate([[base], v, [v[-1], base]]) if base is not None else np.concatenate([v, [v[-1]]])
                ec = p.get_edgecolor(); fc = p.get_facecolor()
                filled = fc[3] > 0 if len(fc) == 4 else False
                lab = p.get_label(); show = not str(lab).startswith("_")
                out.add_trace(go.Scatter(x=xx, y=yy, mode="lines", name=lab if show else "", showlegend=show, xaxis=xs, yaxis=ys,
                                         line=dict(shape="hv", width=px(p.get_linewidth()) if ec[3] > 0 else 0, color=_rgba(ec)),
                                         fill="tozeroy" if filled else None, fillcolor=_rgba(fc) if filled else None))
            elif isinstance(p, Rectangle) and p.get_width() and p.get_height():
                bars_x.append(p.get_x() + p.get_width() / 2); bars_y.append(p.get_height()); bars_w.append(p.get_width()); bars_c.append(_rgba(p.get_facecolor()))
            elif isinstance(p, Polygon):
                xy = p.get_xy(); out.add_trace(go.Scatter(x=xy[:, 0], y=xy[:, 1], mode="lines", fill="toself", showlegend=False, xaxis=xs, yaxis=ys,
                                                           line=dict(width=px(p.get_linewidth()), color=_rgba(p.get_edgecolor())), fillcolor=_rgba(p.get_facecolor())))
        if bars_x:
            out.add_trace(go.Bar(x=bars_x, y=bars_y, width=bars_w, marker=dict(color=bars_c, line=dict(width=0)), showlegend=False, xaxis=xs, yaxis=ys))
            layout["bargap"] = 0
        for c in ax.collections:
            if isinstance(c, QuadMesh):
                coords = c.get_coordinates(); z = c.get_array().reshape(coords.shape[0] - 1, coords.shape[1] - 1)
                xc = 0.5 * (coords[0, 1:, 0] + coords[0, :-1, 0]); yc = 0.5 * (coords[1:, 0, 1] + coords[:-1, 0, 1])
                cmap = c.get_cmap(); vmin, vmax = c.get_clim()
                scale = [[i / 10, _rgba(cmap(i / 10))] for i in range(11)]
                out.add_trace(go.Heatmap(x=xc, y=yc, z=np.asarray(z), zmin=vmin, zmax=vmax, colorscale=scale, showscale=False, xaxis=xs, yaxis=ys))
            elif isinstance(c, LineCollection):
                segs = c.get_segments(); col = _rgba(c.get_colors()[0]) if len(c.get_colors()) else "black"
                xx, yy = [], []
                for s in segs: xx += [s[0][0], s[1][0], None]; yy += [s[0][1], s[1][1], None]
                out.add_trace(go.Scatter(x=xx, y=yy, mode="lines", showlegend=False, xaxis=xs, yaxis=ys,
                                         line=dict(width=px(c.get_linewidths()[0]) if len(c.get_linewidths()) else px(1), color=col)))
            elif isinstance(c, PolyCollection):
                for path in c.get_paths():
                    v = path.vertices
                    out.add_trace(go.Scatter(x=v[:, 0], y=v[:, 1], mode="lines", fill="toself", showlegend=False, xaxis=xs, yaxis=ys,
                                             line=dict(width=0), fillcolor=_rgba(c.get_facecolor()[0])))
            elif isinstance(c, PathCollection):
                off = c.get_offsets(); sizes = c.get_sizes(); fc = c.get_facecolor()
                out.add_trace(go.Scatter(x=off[:, 0], y=off[:, 1], mode="markers", showlegend=not c.get_label().startswith("_"), name=c.get_label(), xaxis=xs, yaxis=ys,
                                         marker=dict(size=[px(np.sqrt(s)) for s in sizes] if len(sizes) > 1 else px(np.sqrt(sizes[0])),
                                                     color=[_rgba(f) for f in fc] if len(fc) > 1 else _rgba(fc[0]))))
        for im in ax.images:
            if isinstance(im, AxesImage):
                a = im.get_array(); ext = im.get_extent(); cmap = im.get_cmap(); vmin, vmax = im.get_clim()
                ny, nx = a.shape[:2]; xc = np.linspace(ext[0], ext[1], nx, endpoint=False) + (ext[1] - ext[0]) / nx / 2
                yc = np.linspace(ext[2], ext[3], ny, endpoint=False) + (ext[3] - ext[2]) / ny / 2
                if im.origin == "upper": yc = yc[::-1]
                out.add_trace(go.Heatmap(x=xc, y=yc, z=np.asarray(a), zmin=vmin, zmax=vmax, colorscale=[[i / 10, _rgba(cmap(i / 10))] for i in range(11)], showscale=False, xaxis=xs, yaxis=ys))
        # ---- texts: place by rendered bbox, so any transform/offset is honoured
        texts = list(ax.texts) + [ax.xaxis.label, ax.yaxis.label, ax.title]
        for t in texts:
            s = t.get_text()
            if not s: continue
            bb = t.get_window_extent(renderer); ha, va = t.get_ha(), t.get_va(); rot = t.get_rotation()
            ax_x = {"left": bb.x0, "center": (bb.x0 + bb.x1) / 2, "right": bb.x1}.get(ha, bb.x0)
            ay = {"bottom": bb.y0, "baseline": bb.y0, "center": (bb.y0 + bb.y1) / 2, "top": bb.y1, "center_baseline": (bb.y0 + bb.y1) / 2}.get(va, bb.y0)
            if rot == 90:   # rotated text: anchor by the rotated box (ha applies vertically)
                ax_x = (bb.x0 + bb.x1) / 2; ay = {"left": bb.y0, "center": (bb.y0 + bb.y1) / 2, "right": bb.y1}.get(ha, bb.y0)
                xa, ya = "center", {"left": "bottom", "center": "middle", "right": "top"}.get(ha, "bottom")
            else:
                xa = {"left": "left", "center": "center", "right": "right"}.get(ha, "left")
                ya = {"bottom": "bottom", "baseline": "bottom", "center": "middle", "top": "top", "center_baseline": "middle"}.get(va, "bottom")
            txt = mathtext_to_html(s)
            if t.get_fontweight() in ("bold", "heavy", 700, 800, 900): txt = f"<b>{txt}</b>"
            if t.get_fontstyle() == "italic": txt = f"<i>{txt}</i>"
            out.add_annotation(text=txt, x=ax_x / W, y=ay / H, xref="paper", yref="paper", xanchor=xa, yanchor=ya,
                               showarrow=False, textangle=-rot, font=dict(size=px(t.get_fontsize()), color=_rgba(t.get_color())))
        # ---- legend
        lg = ax.get_legend()
        if lg is not None:
            bb = lg.get_window_extent(renderer)
            layout["showlegend"] = True
            layout["legend"] = dict(x=bb.x0 / W, y=bb.y1 / H, xanchor="left", yanchor="top", xref="paper", yref="paper",
                                    bgcolor="rgba(0,0,0,0)" if not lg.get_frame_on() else "white", borderwidth=0,
                                    font=dict(size=px(lg.get_texts()[0].get_fontsize()) if lg.get_texts() else px(rc["font.size"])),
                                    itemsizing="constant", tracegroupgap=0)
    out.update_layout(**layout)
    return out


def _mpl_color(c):
    """CSS colour string (rgba()/rgb()/hex/name) -> something matplotlib accepts."""
    if c is None: return None
    if isinstance(c, str):
        m = re.match(r"rgba?\(\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)\s*(?:,\s*([\d.]+))?\s*\)", c)
        if m:
            r, g, b = (float(m.group(i)) / 255 for i in (1, 2, 3)); a = float(m.group(4)) if m.group(4) else 1.0
            return (r, g, b, a)
    return c

# ----------------------------------------------------------------- to_mpl
def to_mpl(pfig: go.Figure, *, dpi: float = 100.0):
    import matplotlib.pyplot as plt
    L = pfig.layout
    W, H = (L.width or 1000), (L.height or 1000)
    fig = plt.figure(figsize=(W / dpi, H / dpi), dpi=dpi)
    pt = lambda p: float(p) * 72.0 / dpi
    fam = (L.font.family or "sans-serif").split(",")[0].strip()
    # axes from the (x, y) axis pairs
    pairs = {}
    for name in L.to_plotly_json().keys():
        if name.startswith("xaxis"):
            suf = name[5:]
            pairs[suf] = (L[name], L["yaxis" + suf] if ("yaxis" + suf) in L.to_plotly_json() else None)
    axes = {}
    for suf, (xa, ya) in pairs.items():
        if ya is None: continue
        xd = xa.domain or (0.125, 0.9); yd = ya.domain or (0.11, 0.88)
        m = L.margin; l = (m.l or 0) / W; r = (m.r or 0) / W; b = (m.b or 0) / H; t = (m.t or 0) / H
        # plotly domains are fractions of the plot area inside the margins
        x0 = l + xd[0] * (1 - l - r); x1 = l + xd[1] * (1 - l - r); y0 = b + yd[0] * (1 - b - t); y1 = b + yd[1] * (1 - b - t)
        ax = fig.add_axes([x0, y0, x1 - x0, y1 - y0]); axes[suf] = ax
        for axis, spec, setter in ((ax.xaxis, xa, ax.set_xlim), (ax.yaxis, ya, ax.set_ylim)):
            if spec.type == "log": axis.axes.set_xscale("log") if axis is ax.xaxis else axis.axes.set_yscale("log")
            if spec.range is not None:
                lo, hi = spec.range
                if spec.type == "log": lo, hi = 10 ** lo, 10 ** hi
                setter(lo, hi)
            if spec.title and spec.title.text:
                (ax.set_xlabel if axis is ax.xaxis else ax.set_ylabel)(html_to_mathtext(spec.title.text), fontsize=pt(spec.title.font.size or L.font.size or 14))
            d = "in" if spec.ticks == "inside" else "out"
            axis.set_tick_params(which="major", direction=d, length=pt(spec.ticklen or 5), width=pt(spec.tickwidth or 1),
                                 labelsize=pt(spec.tickfont.size or L.font.size or 14))
            if spec.minor and spec.minor.ticks:
                axis.set_tick_params(which="minor", direction=d, length=pt(spec.minor.ticklen or 2), width=pt(spec.minor.tickwidth or 1))
                from matplotlib.ticker import AutoMinorLocator
                axis.set_minor_locator(AutoMinorLocator())
            if spec.mirror in ("allticks", True):
                (ax.tick_params(top=True) if axis is ax.xaxis else ax.tick_params(right=True))
            if spec.tickvals is not None:
                axis.set_ticks(list(spec.tickvals))
                if spec.ticktext is not None: axis.set_ticklabels([html_to_mathtext(s) for s in spec.ticktext])
        for sp in ax.spines.values(): sp.set_linewidth(pt(xa.linewidth or 1))
        ax.set_facecolor(_mpl_color(L.plot_bgcolor) or "white")
    fig.patch.set_facecolor(_mpl_color(L.paper_bgcolor) or "white")
    for tr in pfig.data:
        suf = (tr.xaxis or "x")[1:]; ax = axes.get(suf) or axes.get("")
        name = tr.name if getattr(tr, "showlegend", True) and tr.name else "_nolegend_"
        if tr.type == "scatter":
            x = np.asarray(tr.x, dtype=object); y = np.asarray(tr.y, dtype=object)
            shape = (tr.line.shape or "linear"); ds = {"hv": "steps-post", "vh": "steps-pre", "hvh": "steps-mid"}.get(shape, "default")
            col = tr.line.color or (tr.marker.color if isinstance(tr.marker.color, str) else None)
            if tr.fill in ("tozeroy", "toself"):
                xx = np.array([v for v in x if v is not None], float); yy = np.array([v for v in y if v is not None], float)
                ax.fill_between(xx, yy, step="post" if shape == "hv" else None, color=_mpl_color(tr.fillcolor or col), linewidth=0, label=name)
            mode = tr.mode or "lines"
            if "lines" in mode and (tr.line.width is None or tr.line.width > 0):
                ax.plot(x, y, drawstyle=ds, color=_mpl_color(col), linewidth=pt(tr.line.width or 2), linestyle={"dash": "--", "dot": ":", "dashdot": "-."}.get(tr.line.dash, "-"),
                        label=name if "markers" not in mode else "_nolegend_")
            if "markers" in mode:
                ey = tr.error_y.array if tr.error_y and tr.error_y.visible is not False and tr.error_y.array is not None else None
                sym = {"circle": "o", "square": "s", "diamond": "D", "x": "x", "cross": "+", "triangle-up": "^"}.get(tr.marker.symbol or "circle", "o")
                ms = tr.marker.size if isinstance(tr.marker.size, (int, float)) else 6
                mc = tr.marker.color if isinstance(tr.marker.color, str) else col
                if ey is not None:
                    ax.errorbar(np.asarray(x, float), np.asarray(y, float), yerr=np.asarray(ey, float), fmt=sym, color=_mpl_color(mc), markersize=pt(ms), elinewidth=pt(tr.error_y.thickness or 1), capsize=0, label=name)
                elif ms > 0.5:
                    ax.plot(np.asarray(x, float), np.asarray(y, float), linestyle="none", marker=sym, color=_mpl_color(mc), markersize=pt(ms), label=name)
        elif tr.type == "bar":
            ax.bar(tr.x, tr.y, width=tr.width, color=[_mpl_color(c) for c in tr.marker.color] if isinstance(tr.marker.color, (list, tuple)) else _mpl_color(tr.marker.color), linewidth=0, label=name)
        elif tr.type == "heatmap":
            z = np.asarray(tr.z, float); x = np.asarray(tr.x, float); y = np.asarray(tr.y, float)
            xe = np.concatenate([[x[0] - (x[1] - x[0]) / 2], (x[1:] + x[:-1]) / 2, [x[-1] + (x[-1] - x[-2]) / 2]]) if len(x) > 1 else None
            ye = np.concatenate([[y[0] - (y[1] - y[0]) / 2], (y[1:] + y[:-1]) / 2, [y[-1] + (y[-1] - y[-2]) / 2]]) if len(y) > 1 else None
            ax.pcolormesh(xe, ye, z, cmap="viridis", vmin=tr.zmin, vmax=tr.zmax, shading="flat")
    for a in L.annotations or []:
        if not a.text: continue
        if a.xref == "paper" and a.yref == "paper":
            xs = (a.xshift or 0) / W; ys = (a.yshift or 0) / H
            txt = html_to_mathtext(a.text)
            weight = "bold" if "<b>" in (a.text or "") else "normal"; style = "italic" if "<i>" in (a.text or "") else "normal"
            fig.text(a.x + xs, a.y + ys, txt, ha=a.xanchor or "center", va={"top": "top", "middle": "center", "bottom": "bottom"}.get(a.yanchor or "middle", "center"),
                     fontsize=pt(a.font.size or L.font.size or 14), rotation=-(a.textangle or 0), fontweight=weight, fontstyle=style,
                     color=_mpl_color(a.font.color) or "black", family=fam)
    if L.showlegend:
        for ax in axes.values():
            h, l = ax.get_legend_handles_labels()
            if h:
                lg = L.legend; loc = "upper right"
                fs = pt(lg.font.size) if lg and lg.font and lg.font.size else None
                ax.legend(loc=loc, frameon=bool(lg and lg.bgcolor and lg.bgcolor != "rgba(0,0,0,0)"), fontsize=fs)
    return fig
