"""Pixel-diff harness: the same figure through mplhep and through plotlyhep,
rendered to identical pixel grids (10 in x 10 in at 100 dpi = 1000 x 1000), compared.

    python tests/compare.py            # writes tests/output/<case>_{mpl,plotly,diff,side}.png + metrics.json
"""

from __future__ import annotations

import io
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mplhep as hep
import plotly.graph_objects as go
from PIL import Image
from skimage.metrics import structural_similarity as ssim

import plotlyhep as php

OUT = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(7)
BINS = np.linspace(0, 200, 41)
DATA = np.histogram(rng.normal(90, 25, 4000), BINS)[0].astype(float)
MC1 = np.histogram(rng.normal(90, 25, 3000), BINS)[0] * 1.3
MC2 = np.histogram(rng.exponential(60, 3000), BINS)[0] * 0.5


def mpl_fig():
    hep.style.use("CMS")
    fig, ax = plt.subplots(figsize=(10, 10), dpi=100)
    return fig, ax


# ------------------------------------------------------------------ cases
def case_axes_label():
    fig, ax = mpl_fig()
    ax.set_xlim(0, 200)
    ax.set_ylim(0, 400)
    ax.set_xlabel("m$_{jj}$ [GeV]")
    ax.set_ylabel("Events")
    hep.cms.label("Preliminary", data=True, lumi=138, com=13.6, ax=ax, loc=0)
    p = php.figure("CMS")
    p.update_xaxes(range=[0, 200])
    p.update_yaxes(range=[0, 400])
    php.set_xlabel(p, "m<sub>jj</sub> [GeV]")
    php.set_ylabel(p, "Events")
    php.cms.label(p, "Preliminary", data=True, lumi=138, com=13.6, loc=0)
    return fig, p


def case_step_hist():
    fig, ax = mpl_fig()
    hep.histplot([MC1, MC2], BINS, label=["Signal", "Background"], ax=ax)
    hep.histplot(DATA, BINS, yerr=True, histtype="errorbar", color="black", label="Data", ax=ax)
    ax.set_xlim(0, 200)
    ax.set_ylim(0, 450)
    ax.legend(loc="upper right")
    ax.set_xlabel("m$_{jj}$ [GeV]")
    ax.set_ylabel("Events / 5 GeV")
    hep.cms.label("Preliminary", data=True, lumi=138, com=13.6, ax=ax, loc=0)
    p = php.figure("CMS")
    php.histplot(p, [MC1, MC2], BINS, label=["Signal", "Background"])
    php.histplot(p, DATA, BINS, yerr=True, histtype="errorbar", color="black", label="Data")
    p.update_xaxes(range=[0, 200])
    p.update_yaxes(range=[0, 450])
    php.set_xlabel(p, "m<sub>jj</sub> [GeV]")
    php.set_ylabel(p, "Events / 5 GeV")
    php.cms.label(p, "Preliminary", data=True, lumi=138, com=13.6, loc=0)
    return fig, p


def case_inside_label():
    fig, ax = mpl_fig()
    hep.histplot(MC1, BINS, histtype="fill", alpha=0.5, label="Signal", ax=ax)
    ax.set_xlim(0, 200)
    ax.set_ylim(0, 450)
    ax.set_xlabel("m$_{jj}$ [GeV]")
    ax.set_ylabel("Events")
    hep.cms.label("Simulation", data=False, com=13.6, ax=ax, loc=2)
    p = php.figure("CMS")
    php.histplot(p, MC1, BINS, histtype="fill", color="rgba(87,144,252,0.5)", label="Signal")
    p.update_xaxes(range=[0, 200])
    p.update_yaxes(range=[0, 450])
    php.set_xlabel(p, "m<sub>jj</sub> [GeV]")
    php.set_ylabel(p, "Events")
    php.cms.label(p, "Simulation", data=False, com=13.6, loc=2)
    return fig, p


def case_convert_from_mpl():
    """mpl figure -> from_mpl -> Plotly render, against the mpl render of the same figure."""
    from plotlyhep.convert import from_mpl

    fig, _ = case_step_hist()
    return fig, from_mpl(fig)


def case_convert_roundtrip():
    """mpl -> from_mpl -> to_mpl -> mpl render, against the original mpl render (both matplotlib)."""
    from plotlyhep.convert import from_mpl, to_mpl

    fig, _ = case_step_hist()
    fig2 = to_mpl(from_mpl(fig))
    return fig, fig2


def _annotated_mpl():
    fig, ax = mpl_fig()
    hep.histplot(MC1, BINS, label="Signal", ax=ax)
    ax.set_xlim(0, 200)
    ax.set_ylim(0, 450)
    ax.set_xlabel("m$_{jj}$ [GeV]")
    ax.set_ylabel("Events")
    ax.annotate(
        "resonance",
        xy=(90, 340),
        xytext=(140, 400),
        fontsize=22,
        ha="center",
        va="center",
        arrowprops=dict(arrowstyle="->", lw=1.5, color="black"),
    )
    ax.annotate(
        "turn-on",
        xy=(45, 60),
        xytext=(30, 220),
        fontsize=22,
        ha="center",
        va="center",
        arrowprops=dict(arrowstyle="-|>", lw=1.5, color="#e42536"),
    )
    hep.cms.label("Simulation", data=False, com=13.6, ax=ax, loc=0)
    return fig


def case_annotate_from_mpl():
    from plotlyhep.convert import from_mpl

    fig = _annotated_mpl()
    return fig, from_mpl(fig)


def case_annotate_roundtrip():
    from plotlyhep.convert import from_mpl, to_mpl

    fig = _annotated_mpl()
    return fig, to_mpl(from_mpl(fig))


def case_ratio_panel():
    """main + ratio panel: matplotlib gridspec (height_ratios 3:1, hspace 0.05, sharex) under mplhep vs ratio_figure."""
    hep.style.use("CMS")
    fig, (ax, rax) = plt.subplots(2, 1, figsize=(10, 10), dpi=100, sharex=True, gridspec_kw={"height_ratios": [3, 1], "hspace": 0.05})
    hep.histplot(MC1, BINS, label="MC", ax=ax)
    hep.histplot(DATA, BINS, yerr=True, histtype="errorbar", color="black", label="Data", ax=ax)
    ax.set_xlim(0, 200)
    ax.set_ylim(0, 450)
    ax.legend(loc="upper right")
    ax.set_ylabel("Events / 5 GeV")
    r = np.where(MC1 > 0, DATA / np.where(MC1 > 0, MC1, 1), np.nan)
    re = np.where(MC1 > 0, np.sqrt(DATA) / np.where(MC1 > 0, MC1, 1), np.nan)
    rax.errorbar(0.5 * (BINS[1:] + BINS[:-1]), r, yerr=re, fmt=".", color="black", markersize=6, elinewidth=1)
    rax.axhline(1, color="gray", linestyle="--", linewidth=1)
    rax.set_ylim(0.5, 1.5)
    rax.set_ylabel("Data / MC")
    rax.set_xlabel("m$_{jj}$ [GeV]")
    hep.cms.label("Preliminary", data=True, lumi=138, com=13.6, ax=ax, loc=0)
    p = php.ratio_figure("CMS", height_ratios=(3, 1), hspace=0.05)
    php.histplot(p, MC1, BINS, label="MC")
    php.histplot(p, DATA, BINS, yerr=True, histtype="errorbar", color="black", label="Data")
    php.ratioplot(p, DATA, MC1, BINS, band=False)
    p.update_xaxes(range=[0, 200])
    p.update_layout(yaxis=dict(range=[0, 450]))
    php.set_ylabel(p, "Events / 5 GeV")
    php.set_xlabel(p, "m<sub>jj</sub> [GeV]")
    php.cms.label(p, "Preliminary", data=True, lumi=138, com=13.6, loc=0)
    return fig, p


CASES = {
    "axes_label": case_axes_label,
    "step_hist": case_step_hist,
    "inside_label": case_inside_label,
    "ratio_panel": case_ratio_panel,
    "annotate_from_mpl": case_annotate_from_mpl,
    "annotate_roundtrip": case_annotate_roundtrip,
    "convert_from_mpl": case_convert_from_mpl,
    "convert_roundtrip": case_convert_roundtrip,
}


# ------------------------------------------------------------------ render + metrics
def render_mpl(fig) -> np.ndarray:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=100)
    plt.close(fig)
    buf.seek(0)
    return np.asarray(Image.open(buf).convert("L"), dtype=float)


def render_plotly(p) -> np.ndarray:
    png = p.to_image(format="png", width=1000, height=1000, scale=1)
    return np.asarray(Image.open(io.BytesIO(png)).convert("L"), dtype=float)


def metrics(a: np.ndarray, b: np.ndarray) -> dict:
    d = np.abs(a - b)
    return {"mean_abs_diff": float(d.mean()), "frac_pixels_gt40": float((d > 40).mean()), "ssim": float(ssim(a, b, data_range=255.0))}


def run(cases=CASES) -> dict:
    results = {}
    for name, fn in cases.items():
        fig, p = fn()
        A = render_mpl(fig)
        B = render_mpl(p) if not isinstance(p, go.Figure) else render_plotly(p)
        m = metrics(A, B)
        results[name] = m
        Image.fromarray(A.astype(np.uint8)).save(f"{OUT}/{name}_mpl.png")
        Image.fromarray(B.astype(np.uint8)).save(f"{OUT}/{name}_plotly.png")
        Image.fromarray((255 - np.abs(A - B)).astype(np.uint8)).save(f"{OUT}/{name}_diff.png")
        side = np.concatenate([A, np.full((A.shape[0], 20), 128.0), B, np.full((A.shape[0], 20), 128.0), 255 - np.abs(A - B)], axis=1)
        Image.fromarray(side.astype(np.uint8)).save(f"{OUT}/{name}_side.png")
        print(f"{name:14s} mean|Δ|={m['mean_abs_diff']:6.2f}  frac>40={m['frac_pixels_gt40']:.4f}  ssim={m['ssim']:.3f}")
    json.dump(results, open(f"{OUT}/metrics.json", "w"), indent=1)
    return results


if __name__ == "__main__":
    run()
