"""Pixel comparison of the gallery's ROOT-tutorial rebuilds against the tutorial's own output
(reference PNGs from root.cern/doc, tests/reference/). Same pixel grid: df102 renders the
796x672 canvas at scale 3 (2388x2016), df106 the 596x572 canvas at scale 1.
    python tests/compare_root.py      -> tests/output/root_<case>_{ours,side,diff}.png + metrics
"""

from __future__ import annotations

import io
import json
import os
import sys

import numpy as np
from PIL import Image
from skimage.metrics import structural_similarity as ssim

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path[:0] = [os.path.join(ROOT, "src"), os.path.join(ROOT, "docs")]
import root_figures

OUT = os.path.join(HERE, "output")
os.makedirs(OUT, exist_ok=True)
CASES = {
    "df102": (root_figures.dimuon_df102, "df102_NanoAODDimuonAnalysis.png", 3),
    "df106": (root_figures.hzz_df106, "df106_HiggsToFourLeptons.png", 1),
}


def grey(img):
    return np.asarray(img.convert("L"), dtype=float)


def run():
    res = {}
    for name, (fn, ref, scale) in CASES.items():
        fig = fn()
        W, H = fig.layout.width, fig.layout.height
        ours = Image.open(io.BytesIO(fig.to_image(format="png", width=W, height=H, scale=scale)))
        refi = Image.open(os.path.join(HERE, "reference", ref))
        if ours.size != refi.size:
            ours = ours.resize(refi.size, Image.LANCZOS)
        A, B = grey(refi), grey(ours)
        d = np.abs(A - B)
        m = {
            "mean_abs_diff": float(d.mean()),
            "frac_pixels_gt40": float((d > 40).mean()),
            "ssim": float(ssim(A, B, data_range=255.0)),
            "size": list(refi.size),
        }
        res[name] = m
        ours.save(f"{OUT}/root_{name}_ours.png")
        Image.fromarray((255 - d).astype(np.uint8)).save(f"{OUT}/root_{name}_diff.png")
        gap = np.full((A.shape[0], 16), 128.0)
        Image.fromarray(np.concatenate([A, gap, B, gap, 255 - d], 1).astype(np.uint8)).save(f"{OUT}/root_{name}_side.png")
        print(f"{name}: mean|Δ|={m['mean_abs_diff']:.2f} frac>40={m['frac_pixels_gt40']:.4f} ssim={m['ssim']:.3f} @ {refi.size}")
    json.dump(res, open(f"{OUT}/root_metrics.json", "w"), indent=1)
    return res


if __name__ == "__main__":
    run()
