"""Reduce the ATLAS Open Data 13 TeV four-lepton skims (CERN Open Data record 15005) to a
small JSON of m4l histograms per sample and channel, with the official normalisation.

    python docs/make_data.py [cache_dir]          # needs uproot + awkward; ~300 MB download once
Writes docs/data/hzz4l.json. The gallery page is built from that file only (no network in CI).
Selection follows ROOT's df106_HiggsToFourLeptons tutorial."""
from __future__ import annotations

import json
import os
import sys
import urllib.request

import awkward as ak
import numpy as np
import uproot

REC = "https://opendata.cern.ch/record/15005/files/"
INFO = "https://raw.githubusercontent.com/atlas-outreach-data-tools/notebooks-collection-opendata/master/13-TeV-examples/uproot_python/infofile.py"
LUMI_FB = 10.0                                      # ATLAS Open Data 2020 release, 13 TeV, 10 fb-1
EDGES = np.linspace(80, 170, 25)                    # 24 bins of 3.75 GeV, as in df106
SAMPLES = {  # key: (file, group, generator, one-line description)
    "ggH125_ZZ4lep": ("mc_345060.ggH125_ZZ4lep.4lep.root", "Higgs", "Powheg+Pythia8 (NNLOPS)", "gluon–gluon fusion, H → ZZ* → 4ℓ, m_H = 125 GeV — the dominant production mode"),
    "VBFH125_ZZ4lep": ("mc_344235.VBFH125_ZZ4lep.4lep.root", "Higgs", "Powheg+Pythia8", "vector-boson fusion, H → ZZ* → 4ℓ — two forward jets, ~8 % of the signal"),
    "WH125_ZZ4lep": ("mc_341964.WH125_ZZ4lep.4lep.root", "Higgs", "Pythia8", "associated production WH, H → ZZ* → 4ℓ"),
    "ZH125_ZZ4lep": ("mc_341947.ZH125_ZZ4lep.4lep.root", "Higgs", "Pythia8", "associated production ZH, H → ZZ* → 4ℓ"),
    "llll": ("mc_363490.llll.4lep.root", "ZZ*", "Sherpa 2.2.2", "qq̄ → ZZ* → 4ℓ — the irreducible background, same final state as the signal"),
    "Zee": ("mc_361106.Zee.4lep.root", "Z+jets, tt̄", "Powheg+Pythia8", "Z → ee + jets — reducible: extra leptons from heavy flavour or misidentified jets"),
    "Zmumu": ("mc_361107.Zmumu.4lep.root", "Z+jets, tt̄", "Powheg+Pythia8", "Z → μμ + jets — reducible background"),
    "ttbar_lep": ("mc_410000.ttbar_lep.4lep.root", "Z+jets, tt̄", "Powheg+Pythia8", "tt̄ with leptonic decays — reducible background"),
}
DATA = [("data_A.4lep.root", "A"), ("data_B.4lep.root", "B"), ("data_C.4lep.root", "C"), ("data_D.4lep.root", "D")]
GROUPS = {"Higgs": "H → ZZ* → 4ℓ, all production modes (m_H = 125 GeV)",
          "ZZ*": "ZZ* → 4ℓ, irreducible", "Z+jets, tt̄": "Z+jets and tt̄, reducible"}
CHANNELS = {"4e": 44, "4mu": 52, "2e2mu": 48}       # sum of |PDG| types, e=11, mu=13

def fetch(name, cache):
    p = os.path.join(cache, name)
    if not os.path.exists(p):
        print("downloading", name, flush=True); urllib.request.urlretrieve(REC + name, p)
    return p

def select(t, mc):
    cols = ["lep_n", "lep_pt", "lep_eta", "lep_phi", "lep_E", "lep_charge", "lep_type", "trigE", "trigM"]
    if mc: cols += ["mcWeight", "scaleFactor_PILEUP", "scaleFactor_ELE", "scaleFactor_MUON", "scaleFactor_LepTRIGGER"]
    a = t.arrays(cols)
    a = a[(a.trigE | a.trigM) & (a.lep_n == 4)]
    a = a[(ak.sum(a.lep_charge, axis=1) == 0)]
    typ = ak.sum(a.lep_type, axis=1); a = a[(typ == 44) | (typ == 48) | (typ == 52)]
    pt = a.lep_pt / 1000.0
    a = a[(pt[:, 0] > 20) & (pt[:, 1] > 15) & (pt[:, 2] > 10)]
    pt, eta, phi, E = a.lep_pt / 1000.0, a.lep_eta, a.lep_phi, a.lep_E / 1000.0
    px, py, pz = pt * np.cos(phi), pt * np.sin(phi), pt * np.sinh(eta)
    m2 = ak.sum(E, 1) ** 2 - ak.sum(px, 1) ** 2 - ak.sum(py, 1) ** 2 - ak.sum(pz, 1) ** 2
    m4l = np.sqrt(np.maximum(ak.to_numpy(m2), 0))
    chan = ak.to_numpy(ak.sum(a.lep_type, axis=1))
    w = ak.to_numpy(a.mcWeight * a.scaleFactor_PILEUP * a.scaleFactor_ELE * a.scaleFactor_MUON * a.scaleFactor_LepTRIGGER) if mc else np.ones(len(m4l))
    return m4l, chan, w

def hist(m, w, mask=None):
    if mask is not None: m, w = m[mask], w[mask]
    y, _ = np.histogram(m, EDGES, weights=w); y2, _ = np.histogram(m, EDGES, weights=w * w); n, _ = np.histogram(m, EDGES)
    return {"yield": y.tolist(), "sumw2": y2.tolist(), "raw": n.tolist()}

def main(cache):
    os.makedirs(cache, exist_ok=True)
    ns = {}; exec(urllib.request.urlopen(INFO, timeout=60).read().decode(), ns); infos = ns["infos"]
    out = {"source": "ATLAS Open Data, 13 TeV, 2020 release — CERN Open Data record 15005 (four-lepton skims)",
           "normalisation": "xsec [pb] × 10 fb⁻¹ / sumw, from the ATLAS outreach infofile", "lumi_fb": LUMI_FB,
           "selection": "trigger (e or μ); exactly 4 leptons; Σcharge = 0; 4e, 4μ or 2e2μ; pT > 20, 15, 10 GeV (ROOT df106 tutorial)",
           "edges": EDGES.tolist(), "groups": GROUPS, "channels": list(CHANNELS), "samples": {}, "data": {}}
    for key, (fn, group, gen, desc) in SAMPLES.items():
        info = infos[key]; scale = info["xsec"] * LUMI_FB * 1000.0 / info["sumw"]
        with uproot.open(fetch(fn, cache)) as f:
            m, ch, w = select(f["mini"], mc=True)
        w = w * scale
        s = {"group": group, "dsid": info["DSID"], "xsec_pb": info["xsec"], "sumw": info["sumw"], "events_generated": info["events"],
             "generator": gen, "description": desc, "selected_raw": len(m), **hist(m, w),
             "by_channel": {c: hist(m, w, ch == v) for c, v in CHANNELS.items()}}
        out["samples"][key] = s; print(f"{key:16s} {len(m):7d} selected, {sum(s['yield']):8.2f} expected", flush=True)
    md, cd = [], []
    for fn, period in DATA:
        with uproot.open(fetch(fn, cache)) as f:
            m, ch, _ = select(f["mini"], mc=False)
        md.append(m); cd.append(ch)
    m, ch = np.concatenate(md), np.concatenate(cd)
    out["data"] = {"periods": [p for _, p in DATA], "counts": np.histogram(m, EDGES)[0].tolist(), "selected": len(m),
                   "by_channel": {c: np.histogram(m[ch == v], EDGES)[0].tolist() for c, v in CHANNELS.items()}}
    print("data", len(m), "selected events")
    os.makedirs(os.path.join(os.path.dirname(__file__), "data"), exist_ok=True)
    json.dump(out, open(os.path.join(os.path.dirname(__file__), "data", "hzz4l.json"), "w"), indent=0)
    print("wrote docs/data/hzz4l.json")

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..", "site-cache"))
