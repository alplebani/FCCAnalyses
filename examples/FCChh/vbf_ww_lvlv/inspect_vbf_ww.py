#!/usr/bin/env python3
"""
Quick inspection of the Delphes/EDM4hep VBF WW -> lvlv (FCChh_II) output
produced by DelphesPythia8_EDM4HEP. Reads the "events" tree directly with
RDataFrame::AsNumpy and makes a handful of basic kinematic plots: jet
multiplicity, leading/subleading jet pT, dijet mass and delta-eta of the
two leading jets (the classic VBF tag-jet variables), lepton pT, and
missing transverse energy.

Run with the key4hep environment sourced:
    source /cvmfs/sw.hsf.org/key4hep/setup.sh -r 2026-04-08
    python3 inspect_vbf_ww.py [input.edm4hep.root]
(defaults to the output of gen/run_delphes_pythia8.sh)
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import ROOT

INPUT_FILE = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "gen", "mg_pp_vbf_ww_lvlv_5f_84TeV_delphes_scenII.edm4hep.root")
OUTDIR = "plots"


def pt(px, py):
    return np.sqrt(px**2 + py**2)


def eta(px, py, pz):
    p = np.sqrt(px**2 + py**2 + pz**2)
    with np.errstate(divide="ignore", invalid="ignore"):
        return 0.5 * np.log((p + pz) / (p - pz))


def hist(ax, data, bins, range_, label=None, **kwargs):
    ax.hist(data, bins=bins, range=range_, histtype="step", linewidth=1.5,
            label=label, **kwargs)


def main():
    os.makedirs(OUTDIR, exist_ok=True)

    df = ROOT.RDataFrame("events", INPUT_FILE)
    n_events_total = df.Count().GetValue()
    print(f"Events in file: {n_events_total}")

    cols = df.AsNumpy([
        "Jet.momentum.x", "Jet.momentum.y", "Jet.momentum.z", "Jet.energy",
        "ReconstructedParticles.momentum.x", "ReconstructedParticles.momentum.y",
        "ReconstructedParticles.momentum.z", "ReconstructedParticles.energy",
        "Muon_objIdx.index", "Electron_objIdx.index",
        "MissingET.momentum.x", "MissingET.momentum.y",
    ])

    n_jets = []
    lead_jet_pt, sublead_jet_pt = [], []
    mjj, detajj = [], []
    muon_pt, electron_pt = [], []
    met = []

    for i in range(n_events_total):
        jx = np.asarray(cols["Jet.momentum.x"][i])
        jy = np.asarray(cols["Jet.momentum.y"][i])
        jz = np.asarray(cols["Jet.momentum.z"][i])
        je = np.asarray(cols["Jet.energy"][i])
        n_jets.append(len(jx))

        if len(jx) >= 2:
            jpt = pt(jx, jy)
            j1, j2 = np.argsort(jpt)[::-1][:2]

            lead_jet_pt.append(jpt[j1])
            sublead_jet_pt.append(jpt[j2])

            E = je[j1] + je[j2]
            px, py, pz = jx[j1] + jx[j2], jy[j1] + jy[j2], jz[j1] + jz[j2]
            m2 = E**2 - (px**2 + py**2 + pz**2)
            mjj.append(np.sqrt(m2) if m2 > 0 else 0.0)

            detajj.append(abs(eta(jx[j1], jy[j1], jz[j1]) - eta(jx[j2], jy[j2], jz[j2])))

        rx = np.asarray(cols["ReconstructedParticles.momentum.x"][i])
        ry = np.asarray(cols["ReconstructedParticles.momentum.y"][i])

        mu_idx = np.asarray(cols["Muon_objIdx.index"][i], dtype=int)
        if len(mu_idx):
            muon_pt.extend(pt(rx[mu_idx], ry[mu_idx]))

        el_idx = np.asarray(cols["Electron_objIdx.index"][i], dtype=int)
        if len(el_idx):
            electron_pt.extend(pt(rx[el_idx], ry[el_idx]))

        mx = np.asarray(cols["MissingET.momentum.x"][i])
        my = np.asarray(cols["MissingET.momentum.y"][i])
        if len(mx):
            met.append(pt(mx, my)[0])

    n_jets = np.array(n_jets)
    print(f"Mean n_jets: {n_jets.mean():.2f}, events with >=2 jets: "
          f"{(n_jets >= 2).sum()} ({100 * (n_jets >= 2).mean():.1f}%)")
    print(f"Muons found: {len(muon_pt)}, electrons found: {len(electron_pt)}")
    if mjj:
        print(f"Mean m_jj: {np.mean(mjj):.1f} GeV, mean |deta_jj|: {np.mean(detajj):.2f}")

    # 1) jet multiplicity
    fig, ax = plt.subplots()
    hist(ax, n_jets, bins=10, range_=(0, 10))
    ax.set_xlabel("Number of jets")
    ax.set_ylabel("Events")
    fig.savefig(f"{OUTDIR}/n_jets.pdf")

    # 2) leading / subleading jet pT
    fig, ax = plt.subplots()
    hist(ax, lead_jet_pt, bins=50, range_=(0, 500), label="leading jet")
    hist(ax, sublead_jet_pt, bins=50, range_=(0, 500), label="subleading jet")
    ax.set_xlabel("Jet $p_T$ [GeV]")
    ax.set_ylabel("Events")
    ax.legend()
    fig.savefig(f"{OUTDIR}/jet_pt.pdf")

    # 3) dijet invariant mass (VBF tag-jet variable)
    fig, ax = plt.subplots()
    hist(ax, mjj, bins=50, range_=(0, 3000))
    ax.set_xlabel("$m_{jj}$ [GeV] (two leading jets)")
    ax.set_ylabel("Events")
    fig.savefig(f"{OUTDIR}/mjj.pdf")

    # 4) delta-eta between the two leading jets (VBF tag-jet variable)
    fig, ax = plt.subplots()
    hist(ax, detajj, bins=50, range_=(0, 10))
    ax.set_xlabel(r"$|\Delta\eta_{jj}|$ (two leading jets)")
    ax.set_ylabel("Events")
    fig.savefig(f"{OUTDIR}/detajj.pdf")

    # 5) lepton pT (from W -> l nu)
    fig, ax = plt.subplots()
    hist(ax, muon_pt, bins=50, range_=(0, 300), label="muons")
    hist(ax, electron_pt, bins=50, range_=(0, 300), label="electrons")
    ax.set_xlabel("Lepton $p_T$ [GeV]")
    ax.set_ylabel("Leptons")
    ax.legend()
    fig.savefig(f"{OUTDIR}/lepton_pt.pdf")

    # 6) missing transverse energy (from the two neutrinos)
    fig, ax = plt.subplots()
    hist(ax, met, bins=50, range_=(0, 300))
    ax.set_xlabel("Missing $E_T$ [GeV]")
    ax.set_ylabel("Events")
    fig.savefig(f"{OUTDIR}/met.pdf")

    print(f"Plots written to {OUTDIR}/")


if __name__ == "__main__":
    main()
