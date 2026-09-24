"""ATLAS Open Data H -> ZZ* -> 4l, reduced EXACTLY as ROOT's df106_HiggsToFourLeptons tutorial does:
same samples and categories, same selection (isolation, impact parameters, 25/15/10 GeV),
same weights (scale factors x mcWeight x xsec/sumw x 10064 pb-1, ZZ x 1.3) and the same
electron scale-factor variation (up/down) used for the uncertainty band.

    python docs/make_data_root106.py [cache_dir]   -> docs/data/hzz4l_root.json
"""
from __future__ import annotations

import json
import os
import sys
import urllib.request

import awkward as ak
import numpy as np
import uproot

REC = "https://opendata.cern.ch/record/15005/files/"
LUMI_PB = 10064.0
EDGES = np.linspace(80, 170, 25)
SAMPLES = {  # from df106_HiggsToFourLeptons_spec.json
    "mc_345060.ggH125_ZZ4lep": ("higgs", 0.0060239, 27881776.6536, 1.0, "Powheg+Pythia8 (NNLOPS)", "gluon–gluon fusion, H → ZZ* → 4ℓ, m_H = 125 GeV"),
    "mc_344235.VBFH125_ZZ4lep": ("higgs", 0.0004633012, 3680490.83243, 1.0, "Powheg+Pythia8", "vector-boson fusion, H → ZZ* → 4ℓ"),
    "mc_363490.llll": ("zz", 1.2578, 7538705.8077, 1.3, "Sherpa 2.2.2", "qq̄ → ZZ* → 4ℓ, irreducible (× 1.3 for the missing gg → ZZ)"),
    "mc_361106.Zee": ("other", 1950.5295, 150277594200.0, 1.0, "Powheg+Pythia8", "Z → ee + jets, reducible"),
    "mc_361107.Zmumu": ("other", 1950.6321, 147334691090.0, 1.0, "Powheg+Pythia8", "Z → μμ + jets, reducible"),
}
DATA = ["data_A", "data_B", "data_C", "data_D"]
# VaryHelper: electron scale-factor uncertainty vs pT (MeV), linearly interpolated
VX = np.array([5.50e3, 5.52e3, 12.54e3, 17.43e3, 22.40e3, 27.48e3, 30e3, 10000e3]); VY = np.array([0.06628, 0.06395, 0.06396, 0.03372, 0.02441, 0.01403, 0, 0])

def fetch(name, cache):
    p = os.path.join(cache, name + ".4lep.root")
    if not os.path.exists(p):
        print("downloading", name, flush=True); urllib.request.urlretrieve(REC + name + ".4lep.root", p)
    return p

def run(t, mc):
    cols = ["lep_pt", "lep_eta", "lep_phi", "lep_E", "lep_charge", "lep_type", "trigE", "trigM", "lep_ptcone30", "lep_etcone20",
            "lep_trackd0pvunbiased", "lep_tracksigd0pvunbiased", "lep_z0"]
    if mc: cols += ["mcWeight", "scaleFactor_PILEUP", "scaleFactor_ELE", "scaleFactor_MUON", "scaleFactor_LepTRIGGER"]
    a = t.arrays(cols)
    a = a[a.trigE | a.trigM]
    good = (abs(a.lep_eta) < 2.5) & (a.lep_pt > 5000) & (a.lep_ptcone30 / a.lep_pt < 0.3) & (a.lep_etcone20 / a.lep_pt < 0.3)
    keep = ak.sum(good, axis=1) == 4; a, good = a[keep], good[keep]
    keep = ak.sum(a.lep_charge[good], axis=1) == 0; a, good = a[keep], good[keep]
    st = ak.sum(a.lep_type[good], axis=1); keep = (st == 44) | (st == 52) | (st == 48); a, good = a[keep], good[keep]
    # GoodElectronsAndMuons: impact parameters, electron pT/eta
    pt, eta, phi, E = a.lep_pt[good], a.lep_eta[good], a.lep_phi[good], a.lep_E[good]
    typ, d0, sd0, z0 = a.lep_type[good], a.lep_trackd0pvunbiased[good], a.lep_tracksigd0pvunbiased[good], a.lep_z0[good]
    theta = 2 * np.arctan(np.exp(-eta)); ipok = (abs(d0 / sd0) <= 5) & (abs(z0 * np.sin(theta)) <= 0.5)
    eok = (typ != 11) | ((pt >= 7000) & (abs(eta) <= 2.47))
    keep = ak.all(ipok & eok, axis=1); a, good = a[keep], good[keep]
    pt = a.lep_pt[good]; keep = (pt[:, 0] > 25000) & (pt[:, 1] > 15000) & (pt[:, 2] > 10000); a, good = a[keep], good[keep]
    pt, eta, phi, E, typ = (x[good] for x in (a.lep_pt, a.lep_eta, a.lep_phi, a.lep_E, a.lep_type))
    px, py, pz = pt * np.cos(phi), pt * np.sin(phi), pt * np.sinh(eta)
    m2 = ak.sum(E, 1) ** 2 - ak.sum(px, 1) ** 2 - ak.sum(py, 1) ** 2 - ak.sum(pz, 1) ** 2
    m4l = 0.001 * np.sqrt(np.maximum(ak.to_numpy(m2), 0))
    if not mc:
        return m4l, np.ones(len(m4l)), np.zeros(len(m4l))
    w = ak.to_numpy(a.scaleFactor_ELE * a.scaleFactor_MUON * a.scaleFactor_LepTRIGGER * a.scaleFactor_PILEUP * a.mcWeight)
    # variation: mean over electrons of the interpolated uncertainty (0 if no electrons)
    ept = pt[typ == 11]
    v = np.array([np.interp(ak.to_numpy(e), VX, VY).mean() if len(e) else 0.0 for e in ept])
    return m4l, w, v

def H(m, w): return np.histogram(m, EDGES, weights=w)[0]

def main(cache):
    out = {"source": "ATLAS Open Data 13 TeV (CERN Open Data record 15005), reduced as ROOT's df106_HiggsToFourLeptons", "lumi_pb": LUMI_PB,
           "edges": EDGES.tolist(), "samples": {}, "categories": {}, "data": {}}
    cat = {"higgs": np.zeros(24), "zz": np.zeros(24), "other": np.zeros(24)}
    nom, up, dn, sumw2 = np.zeros(24), np.zeros(24), np.zeros(24), np.zeros(24)
    for name, (c, xs, sw, sc, gen, desc) in SAMPLES.items():
        with uproot.open(fetch(name, cache)) as f:
            m, w, v = run(f["mini"], True)
        w = w * sc * xs / sw * LUMI_PB
        h = H(m, w); cat[c] += h; nom += h; up += H(m, (1 + v) * w); dn += H(m, (1 - v) * w); sumw2 += H(m, w * w)
        out["samples"][name] = {"category": c, "xsec_pb": xs, "sumw": sw, "scale": sc, "generator": gen, "description": desc,
                                "selected_raw": len(m), "yield": h.tolist(), "raw": np.histogram(m, EDGES)[0].tolist()}
        print(f"{name:28s} {len(m):7d} selected, {h.sum():8.3f} expected", flush=True)
    out["categories"] = {k: v.tolist() for k, v in cat.items()}
    out["mc_total"] = {"nominal": nom.tolist(), "up": up.tolist(), "down": dn.tolist(), "sumw2": sumw2.tolist()}
    md = []
    for d in DATA:
        with uproot.open(fetch(d, cache)) as f:
            m, _, _ = run(f["mini"], False)
        md.append(m)
    m = np.concatenate(md); out["data"] = {"counts": np.histogram(m, EDGES)[0].tolist(), "selected": len(m)}
    print("data", len(m), "selected; MC total", round(nom.sum(), 2))
    os.makedirs(os.path.join(os.path.dirname(__file__), "data"), exist_ok=True)
    json.dump(out, open(os.path.join(os.path.dirname(__file__), "data", "hzz4l_root.json"), "w"), indent=0)
    print("wrote docs/data/hzz4l_root.json")

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..", "site-cache"))
