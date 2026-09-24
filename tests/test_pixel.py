"""Ratchet: every case must stay at or under the thresholds in thresholds.json.
Tighten the numbers whenever the mirror improves; never loosen without a reason in the commit."""
import json
import os

import pytest

from compare import CASES, run

TH = json.load(open(os.path.join(os.path.dirname(__file__), "thresholds.json")))
RES = run()

@pytest.mark.parametrize("name", list(CASES))
def test_pixel_diff(name):
    m, t = RES[name], TH[name]
    assert m["mean_abs_diff"] <= t["mean_abs_diff"], f"{name}: mean|Δ| {m['mean_abs_diff']:.2f} > {t['mean_abs_diff']}"
    assert m["frac_pixels_gt40"] <= t["frac_pixels_gt40"], f"{name}: frac>40 {m['frac_pixels_gt40']:.4f} > {t['frac_pixels_gt40']}"
    assert m["ssim"] >= t["ssim"], f"{name}: ssim {m['ssim']:.3f} < {t['ssim']}"
