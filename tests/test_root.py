"""Ratchet on the ROOT-tutorial rebuilds vs the tutorial's own output images."""
import json, os, pytest
from compare_root import run, CASES
TH = json.load(open(os.path.join(os.path.dirname(__file__), "thresholds_root.json")))
RES = run()

@pytest.mark.parametrize("name", list(CASES))
def test_root_rebuild(name):
    m, t = RES[name], TH[name]
    assert m["mean_abs_diff"] <= t["mean_abs_diff"], f"{name}: mean|Δ| {m['mean_abs_diff']:.2f} > {t['mean_abs_diff']}"
    assert m["ssim"] >= t["ssim"], f"{name}: ssim {m['ssim']:.3f} < {t['ssim']}"
