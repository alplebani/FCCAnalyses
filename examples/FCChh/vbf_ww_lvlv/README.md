# mg_pp_vbf_ww_lvlv_5f_84TeV — from LHE to plots

Pythia8 + Delphes fast-sim and the FCCAnalyses chain for the MadGraph LHE sample

```
/eos/experiment/fcc/hh/generation/lhe/mg_pp_vbf_ww_lvlv_5f_84TeV/events_*.lhe.gz
```

i.e. `p p > j j l v l v` (VBF production of `W W -> l v l v`), 5-flavor scheme,
LO, `sqrt(s) = 84 TeV`, 10000 events per fragment, 100 fragments total.

Three stages, in order:
1. **`gen/`** — Pythia8 card + single-fragment Pythia8+Delphes run.
2. **`condor/`** — the same step for all 100 fragments via HTCondor.
3. **`analysis_*.py`** — `fccanalysis` stage1 → final → plots chain over the
   condor output.

## Directory structure

```
vbf_ww_lvlv/
├── README.md
├── gen/
│   ├── mg_pp_vbf_ww_lvlv_5f_84TeV.cmd   <- the Pythia8 card (single source of truth)
│   └── run_delphes_pythia8.sh           <- stage 1: single fragment
├── condor/                              <- stage 2: scale-out
│   ├── fragments.txt / fragments_test.txt
│   ├── run_fragment.sh
│   └── submit.sub
├── inspect_vbf_ww.py                    <- quick plots without FCCAnalyses
├── analysis_config.py                   <- stage 3: fccanalysis
├── analysis_stage1.py
├── analysis_final.py
├── analysis_plots.py
└── feynman/                             <- VBS W+W- Feynman diagrams (TikZ-Feynman)
```

`.root` outputs, `plots/`, `condor/logs/` and the per-job cards are git-ignored.

---

## Stage 1: `gen/` — Pythia8 card and single-fragment run

`DelphesPythia8_EDM4HEP` is a standalone Delphes executable (ships with
key4hep, no Gaudi/`k4run`) that showers the LHE file with Pythia8 **and**
runs the Delphes fast-sim in one step, writing EDM4hep output directly — see
the [FCC-hh software tutorial](https://indico.cern.ch/event/1467696/contributions/6179879/attachments/2950056/5185386/2024-10-17_FCChhPPMeeting_software_tutorial.pdf)
and the [Delphes workbook](https://delphes.github.io/workbook/pythia8/).

```
DelphesPythia8_EDM4HEP <delphes_card> <edm4hep_output_config> <pythia_card> <output_file>
```

- `mg_pp_vbf_ww_lvlv_5f_84TeV.cmd` — Pythia8 card, structured after
  [`tester_pwp8_pp_hh_5f_hhbbyy.cmd`](https://github.com/HEP-FCC/GenToAna-Tutorial/blob/main/Gen/hh/tester_pwp8_pp_hh_5f_hhbbyy.cmd),
  minus the `ResonanceDecayFilter`/`POWHEG:*` block (this sample is LO and
  `W -> l v` is already fixed in the LHE). Its `Beams:LHEF` points at one
  fragment; `condor/run_fragment.sh` swaps that per job.
- `run_delphes_pythia8.sh` — sources key4hep `-r 2026-04-08` and runs
  `DelphesPythia8_EDM4HEP` with the FCC-hh scenario II card.

**Run:**
```bash
./gen/run_delphes_pythia8.sh [output_file]
```
Default output: `gen/mg_pp_vbf_ww_lvlv_5f_84TeV_delphes_scenII.edm4hep.root`.
Takes several minutes for 10000 events.

> **Gotcha:** the scripts don't use `set -u` — key4hep's `setup.sh`
> references an unset variable internally and aborts under it.

**Output collections** (from `$K4SIMDELPHES/edm4hep_output_config.tcl`):

| Collection | Content | Type |
|---|---|---|
| `ReconstructedParticles` | merged particle-flow candidates | direct `ReconstructedParticle` collection |
| `Jet` | jets from particle-flow candidates | direct collection, plus `Jet_HF_tags`/`Jet_tau_tags` |
| `Muon`, `Electron`, `Photon` | identified leptons/photons | **subset** collections — dereference via `<Collection>_objIdx.index` into `ReconstructedParticles` |
| `MissingET` | event MET | direct collection, 1 entry/event |
| `ScalarHT` | scalar sum of transverse energy | 1 entry/event |
| `Particle` | generator-level particles | `MCParticle` collection |
| `RecoMCLink` | reco ↔ gen associations | `podio::Link<ReconstructedParticle, MCParticle>` |

### What to change

| Want to... | Change this |
|---|---|
| Run a different LHE fragment | `Beams:LHEF` in the `.cmd` card |
| Fewer/more events | `Main:numberOfEvents` in the `.cmd` card (no `-n` CLI override for this binary) |
| A different generator sample | Point `Beams:LHEF` at it; add `ResonanceDecayFilter`/`POWHEG:*` blocks if it needs forced decays or is NLO-matched |
| A different detector/scenario | 1st arg to `DelphesPythia8_EDM4HEP` — alternatives under `$DELPHES_DIR/cards/` |
| Which collections are written | Copy `$K4SIMDELPHES/edm4hep_output_config.tcl`, edit, pass as 2nd arg |
| Classic Delphes ROOT tree instead of EDM4hep | Use `DelphesPythia8` (3 args) instead |

---

## Stage 2: `condor/` — all fragments on HTCondor

One job per LHE fragment, each running the same `DelphesPythia8_EDM4HEP`
step with the card from `gen/` (its `Beams:*` lines replaced by the job's
fragment). Output goes to `$OUTPUT_DIR/<fragment>.edm4hep.root`, by default
`/eos/home-a/alpleban/FCC/vbf_ww_lvlv/samples/mg_pp_vbf_ww_lvlv_5f_84TeV` —
the directory `analysis_config.py`'s `input_dir` points at.

- `fragments.txt` — all 100 LHE fragments; `fragments_test.txt` — small test subset.
- `run_fragment.sh` — skips fragments whose output already exists (safe to
  resubmit after a partial failure).
- `submit.sub` — `request_memory = 2GB`, `+JobFlavour = "workday"`
  (~20-25 min/job actual).

**Submit** (needs CERN's EosSubmit schedds when the repo lives on `/eos`):
```bash
module load lxbatch/eossubmit
cd condor/
mkdir -p logs
export OUTPUT_DIR=/eos/user/<x>/<you>/vbf_ww_lvlv/samples/mg_pp_vbf_ww_lvlv_5f_84TeV  # your own area
condor_submit submit.sub
```
Then point `input_dir` in `analysis_config.py` at the parent of `$OUTPUT_DIR`.

**Monitor:**
```bash
condor_q
tail -f logs/<ClusterId>.log
ls $OUTPUT_DIR | wc -l
```

| Want to... | Change this |
|---|---|
| Process a subset | `queue lhefile from fragments_test.txt` in `submit.sub` |
| Resource requests | `request_cpus`/`request_memory`/`+JobFlavour` in `submit.sub` |
| Pythia8 settings | `gen/mg_pp_vbf_ww_lvlv_5f_84TeV.cmd` (shared with stage 1) |
| Merge into one file (optional — `fccanalysis` reads a directory natively) | `hadd merged.edm4hep.root $OUTPUT_DIR/*.root` |

---

## Quick look: `inspect_vbf_ww.py`

Reads the EDM4hep output with `ROOT.RDataFrame(...).AsNumpy(...)` — no
FCCAnalyses build needed — and writes `n_jets`, `jet_pt`, `mjj`, `detajj`,
`lepton_pt`, `met` plots to `plots/`.

```bash
source /cvmfs/sw.hsf.org/key4hep/setup.sh -r 2026-04-08
python3 inspect_vbf_ww.py [input.edm4hep.root]
```

Example (one fragment, 10000 events):
```
Mean n_jets: 3.64, events with >=2 jets: 9318 (93.2%)
Muons found: 7367, electrons found: 5706
Mean m_jj: 568.1 GeV, mean |deta_jj|: 2.47
```

---

## Stage 3: FCCAnalyses chain

Modeled on `examples/FCChh/vbf_hww/`:

| File | Stage | What it does |
|---|---|---|
| `analysis_config.py` | shared | Process list, input/output dirs |
| `analysis_stage1.py` | `fccanalysis run` | Physics-object/kinematic variables, loose preselection (1e, 1μ, ≥2 jets, truth `W+W-`), flat ntuple |
| `analysis_final.py` | `fccanalysis final` | Cross-section/lumi scaling + `cutList` cutflow |
| `analysis_plots.py` | `fccanalysis plots` | One plot per variable per selection stage |

**Gotchas:**
- **Use key4hep `-r 2024-10-03`, not `-r 2026-04-08`** — this FCCAnalyses
  build is linked against ROOT 6.32; ROOT 6.38 segfaults in cppyy on startup.
- **Set `PYTHONPATH`** — the scripts `import vbf_ww_lvlv.analysis_config`,
  which needs `examples/FCChh/` on `sys.path`.

**Run** (from the FCCAnalyses root):
```bash
source /cvmfs/sw.hsf.org/key4hep/setup.sh -r 2024-10-03
source ./setup.sh
export PYTHONPATH=$PWD/examples/FCChh:$PYTHONPATH

fccanalysis run   examples/FCChh/vbf_ww_lvlv/analysis_stage1.py
fccanalysis final examples/FCChh/vbf_ww_lvlv/analysis_final.py
fccanalysis plots examples/FCChh/vbf_ww_lvlv/analysis_plots.py
```

| Want to... | Change this |
|---|---|
| Your own input/output area | `input_dir`, `*_output` in `analysis_config.py` |
| Add fragments/processes | `process_list` in `analysis_config.py`; new backgrounds also need `procDictAdd` in `analysis_final.py` and `procs`/`colors`/`legend` in `analysis_plots.py` |
| Change preselection | `.Filter(...)` chain in `analysis_stage1.py` |
| Add a variable | `.Define(...)` + `output()` in `analysis_stage1.py`, `histoList` in `analysis_final.py` |
| Change the cutflow | `cutList` in `analysis_final.py` (keep `extralabel` in `analysis_plots.py` in sync) |
| Luminosity/cross-section | `intLumi`/`procDictAdd[...]['crossSection']` in `analysis_final.py` (11.8889861497 pb) |

---

## Feynman diagrams: `feynman/`

`vbs_ww_diagrams.pdf` — one page per diagram class (overview, quartic,
s/t-channel γ/Z, s/t-channel Higgs, non-VBS EW). Rebuild with
`pdflatex vbs_ww_diagrams.tex`.
