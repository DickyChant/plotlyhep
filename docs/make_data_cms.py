"""Reduce CMS Open Data dimuon events to a log-binned invariant-mass spectrum (JSON).

    python docs/make_data_cms.py 2010 [cache_dir]   # record 700:   100k dimuon events, Run2010B, CSV (15 MB), seconds
    python docs/make_data_cms.py 2012 [cache_dir]   # record 12341: Run2012B+C DoubleMuParked, NanoAOD-like ROOT (2.24 GB), minutes

Both merge into docs/data/dimuon.json under their own key. The gallery reads that file only."""
from __future__ import annotations
import json, os, sys, urllib.request
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "data", "dimuon.json")
EDGES = np.logspace(np.log10(0.25), np.log10(300.0), 901)          # ~290 bins per decade
SRC = {
    "2010": ("https://opendata.cern.ch/record/700/files/MuRun2010B.csv", "MuRun2010B.csv",
             "CMS Open Data record 700 — 100k dimuon events selected from the Run2010B Mu primary dataset (7 TeV)"),
    "2012": ("https://opendata.cern.ch/record/12341/files/Run2012BC_DoubleMuParked_Muons.root", "Run2012BC_DoubleMuParked_Muons.root",
             "CMS Open Data record 12341 — Run2012B+C DoubleMuParked, reduced to muons in NanoAOD format (8 TeV, 61.5 M events)"),
}
RESONANCES = [  # name, mass GeV, width, what it is, note
    ("η", 0.5479, "1.31 keV", "light-quark pseudoscalar meson (uū, dd̄, ss̄)", "μμ branching ratio ~6×10⁻⁶ — barely visible even with 61 M events"),
    ("ρ / ω", 0.7753, "149 MeV / 8.7 MeV", "light vector mesons, unresolved from each other here", "the first bump of the spectrum"),
    ("φ", 1.0195, "4.2 MeV", "ss̄ vector meson", "μμ branching ratio 2.9×10⁻⁴"),
    ("J/ψ", 3.0969, "93 keV", "cc̄ 1S — the November 1974 revolution (BNL and SLAC)", "μμ branching ratio 6 % — the tallest narrow peak in the spectrum"),
    ("ψ(2S)", 3.6861, "294 keV", "cc̄ 2S, the first radial excitation", "μμ branching ratio 0.8 %"),
    ("Υ(1S)", 9.4603, "54 keV", "bb̄ 1S — Fermilab 1977, the discovery of the b quark", "μμ branching ratio 2.5 %"),
    ("Υ(2S)", 10.0233, "32 keV", "bb̄ 2S", "resolved from the 1S and 3S by the CMS muon resolution"),
    ("Υ(3S)", 10.3552, "20 keV", "bb̄ 3S", ""),
    ("Z", 91.1876, "2.495 GeV", "the neutral weak boson — CERN 1983 (UA1, UA2)", "μμ branching ratio 3.4 %; the width here is the natural width, not resolution"),
]

def fetch(url, name, cache):
    os.makedirs(cache, exist_ok=True); p = os.path.join(cache, name)
    if not os.path.exists(p):
        print("downloading", name, flush=True); urllib.request.urlretrieve(url, p)
    return p

def hist(m, sel):
    return np.histogram(m[sel], EDGES)[0].tolist()

def reduce_2010(cache):
    url, name, desc = SRC["2010"]; p = fetch(url, name, cache)
    import csv
    E1 = []; P1 = []; E2 = []; P2 = []; Q = []
    with open(p) as f:
        r = csv.DictReader(f); keys = [k.strip() for k in r.fieldnames]; r.fieldnames = keys
        for row in r:
            E1.append(float(row["E1"])); P1.append((float(row["px1"]), float(row["py1"]), float(row["pz1"])))
            E2.append(float(row["E2"])); P2.append((float(row["px2"]), float(row["py2"]), float(row["pz2"])))
            Q.append(int(row["Q1"]) * int(row["Q2"]))
    E1, E2, P1, P2, Q = map(np.asarray, (E1, E2, P1, P2, Q))
    m2 = (E1 + E2) ** 2 - ((P1 + P2) ** 2).sum(1); m = np.sqrt(np.maximum(m2, 0))
    return {"description": desc, "sqrt_s_TeV": 7, "n_events": int(len(m)), "os": hist(m, Q < 0), "ss": hist(m, Q > 0)}

def reduce_2012(cache):
    import uproot, awkward as ak
    url, name, desc = SRC["2012"]; p = fetch(url, name, cache)
    os_c = np.zeros(len(EDGES) - 1); ss_c = np.zeros(len(EDGES) - 1); n = 0
    for a in uproot.iterate(p + ":Events", ["nMuon", "Muon_pt", "Muon_eta", "Muon_phi", "Muon_mass", "Muon_charge"], step_size="300 MB"):
        n += len(a); a = a[a.nMuon == 2]
        pt, eta, phi, mass, q = (a[k] for k in ("Muon_pt", "Muon_eta", "Muon_phi", "Muon_mass", "Muon_charge"))
        px, py, pz = pt * np.cos(phi), pt * np.sin(phi), pt * np.sinh(eta); E = np.sqrt(px ** 2 + py ** 2 + pz ** 2 + mass ** 2)
        m2 = ak.sum(E, 1) ** 2 - ak.sum(px, 1) ** 2 - ak.sum(py, 1) ** 2 - ak.sum(pz, 1) ** 2
        m = np.sqrt(np.maximum(ak.to_numpy(m2), 0)); qq = ak.to_numpy(ak.prod(q, axis=1))
        os_c += np.histogram(m[qq < 0], EDGES)[0]; ss_c += np.histogram(m[qq > 0], EDGES)[0]
        print(f"  {n/1e6:6.1f} M events read", flush=True)
    return {"description": desc, "sqrt_s_TeV": 8, "n_events": int(n), "os": os_c.astype(int).tolist(), "ss": ss_c.astype(int).tolist()}

ROOT_EDGES = np.linspace(0.25, 300.0, 30001)                     # ROOT df102: 30000 uniform bins

def main(which, cache):
    global EDGES
    out = json.load(open(OUT)) if os.path.exists(OUT) else {"edges": EDGES.tolist(), "resonances": [dict(zip(("name", "mass", "width", "what", "note"), r)) for r in RESONANCES], "datasets": {}}
    if which == "2012root":                                        # ROOT-tutorial binning, for the identical plot
        EDGES = ROOT_EDGES; d = reduce_2012(cache); d["edges"] = "root"; out["root_edges"] = [0.25, 300.0, 30000]
        out["datasets"]["2012_root"] = d; which = "2012_root"
    else:
        out["datasets"][which] = reduce_2010(cache) if which == "2010" else reduce_2012(cache)
    os.makedirs(os.path.dirname(OUT), exist_ok=True); json.dump(out, open(OUT, "w"))
    d = out["datasets"][which]; print(f"{which}: {d['n_events']} events, {sum(d['os'])} opposite-sign pairs in [0.25, 300] GeV -> {OUT}")

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "site-cache"))
