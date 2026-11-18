# mg_pp_vbf_ww_lvlv_5f_84TeV — from LHE to plots

Pythia8 + Delphes fast-sim and the FCCAnalyses chain for the MadGraph LHE sample

```
/eos/experiment/fcc/hh/generation/lhe/mg_pp_vbf_ww_lvlv_5f_84TeV/events_*.lhe.gz
```

i.e. `p p > j j l v l v` (VBF production of `W W -> l v l v`), 5-flavor scheme,
LO, `sqrt(s) = 84 TeV`, 10000 events per fragment, 100 fragments total.

Three stages, in order:
1. **`gen/`** — Pythia8 card + single-fragment Pythia8+Delphes run.
2. **`condor_submit.py`** — the same step for all 100 fragments via HTCondor.
3. **`analysis_*.py`** — `fccanalysis` stage1 → final → plots chain over the
   condor output.

## Directory structure

```
vbf_ww_lvlv/
├── README.md
├── gen/
│   ├── mg_pp_vbf_ww_lvlv_5f_84TeV.cmd   <- the Pythia8 card (single source of truth)
│   ├── run_fragment.sh                  <- stage 1: any single LHE fragment (also used by condor)
│   └── run_delphes_pythia8.sh           <- stage 1: the fragment set in the card's Beams:LHEF
├── condor_submit.py                     <- stage 2: writes condor/<folder>/ and submits
├── condor/
│   ├── fragments.txt                    <- all 100 LHE fragments
│   └── <folder>/                        <- one per submission (generated)
│       ├── run_fragment.sh / submit.sub
│       └── outputs/ errors/ logs/
├── inspect_vbf_ww.py                    <- quick plots without FCCAnalyses
├── analysis_config.py                   <- stage 3: fccanalysis
├── analysis_stage1.py
├── analysis_final.py
├── analysis_plots.py
└── feynman/                             <- VBS W+W- Feynman diagrams (TikZ-Feynman)
```

`.root` outputs, `plots/`, the `condor/<folder>/` submission folders and the
per-fragment `pythia_*.cmd` cards are git-ignored.

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
  fragment; `run_fragment.sh` swaps that for the fragment it is given.
- `run_fragment.sh` — runs on any LHE fragment: writes a copy of the card
  with its `Beams:*` lines pointing at that fragment (`pythia_<fragment>.cmd`,
  in the current directory), sources key4hep (`$KEY4HEP_SETUP`) and runs
  `DelphesPythia8_EDM4HEP` with the FCC-hh scenario II track-covariance card
  (`$DELPHES_CARD`), see below. Skips the fragment if its output already
  exists, fails if the LHE file is missing, and ends with `Job FINISHED` or
  `Job FAILED`. This is also what every condor job runs (stage 2).
- `run_delphes_pythia8.sh` — the same, but on the fragment set in the card's
  `Beams:LHEF`.

**Run:**
```bash
./gen/run_fragment.sh <lhe_file> [output_dir]
# e.g.
./gen/run_fragment.sh /eos/experiment/fcc/hh/generation/lhe/mg_pp_vbf_ww_lvlv_5f_84TeV/events_001453574.lhe.gz out/
```
Output: `<output_dir>/<fragment>.edm4hep.root` (`output_dir` defaults to the
current directory). Takes ~20-25 min for the 10000 events of a fragment.

Or, for the fragment in the card:
```bash
./gen/run_delphes_pythia8.sh [output_file]
```
Default output: `gen/mg_pp_vbf_ww_lvlv_5f_84TeV_delphes_scenII_TrackCov.edm4hep.root`.

### Detector card and software environment

Step-by-step instructions for producing and analysing the samples with this
card: [`README_TrackCov.md`](README_TrackCov.md).

Both `gen/run_fragment.sh` and `gen/run_delphes_pythia8.sh` take these from
the environment, falling back to the defaults below (for condor, pass them as
`--delphes-card` / `--key4hep-setup` to `condor_submit.py` instead):

| Variable | Default | Meaning |
|---|---|---|
| `DELPHES_CARD` | `$DELPHES_DIR/cards/FCC/scenarios/FCChhTrackCov_II.tcl` | Delphes detector card |
| `KEY4HEP_SETUP` | `/cvmfs/sw-nightlies.hsf.org/key4hep/setup.sh --spack -r 2026-10-20` | key4hep setup script **plus its options** |

**Why a nightly:** `FCChhTrackCov_II.tcl` replaces the simple momentum
smearing of `FCChh_II.tcl` with full track-covariance smearing
(`TrackCovariance` module). With the latest stable key4hep release
(`2026-04-08`) Delphes aborts after ~10 events
(`SolTrack::KalmanCov: Error matrix not positive definite` →
`TrkUtil::CovSmear: covariance matrix has negative diagonal elements. Aborting.`,
then a segfault). This is a Delphes bug fixed upstream on 2026-05-11
("Set protection for numerical instability in Kalman calculation of track
parameter covariance matrix"), which no stable release contains yet. The
date-pinned nightly above has the fix and runs cleanly; its output is read
fine by the FCCAnalyses setup in stage 3.

> **Gotcha:** key4hep is retiring the Spack nightlies ("The --spack option
> will soon fail"). When that happens, or once a stable release newer than
> 2026-05-11 exists, override the setup instead of editing the scripts:
> ```bash
> export KEY4HEP_SETUP="/cvmfs/sw.hsf.org/key4hep/setup.sh -r <newer-release>"
> # or the rolling (weekly-changing, not reproducible) nightly:
> export KEY4HEP_SETUP="/cvmfs/sw-nightlies.hsf.org/key4hep/setup.sh"
> ```

To reproduce the original samples (the plain scenario II card, which works
on the stable release):
```bash
python3 condor_submit.py -f FCChh_II \
    -o /eos/user/<x>/<you>/vbf_ww_lvlv/samples/mg_pp_vbf_ww_lvlv_5f_84TeV \
    --delphes-card /cvmfs/sw.hsf.org/key4hep/releases/2026-04-08/x86_64-almalinux9-gcc14.2.0-opt/delphes/master-e2vu45/cards/FCC/scenarios/FCChh_II.tcl \
    --key4hep-setup "/cvmfs/sw.hsf.org/key4hep/setup.sh -r 2026-04-08"
```
(the card must be a full path: `$DELPHES_DIR` is only defined after the
setup script has run inside the job.)

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
| Run a different LHE fragment | Pass it to `gen/run_fragment.sh` (or set `Beams:LHEF` in the `.cmd` card for `run_delphes_pythia8.sh`) |
| Fewer/more events | `Main:numberOfEvents` in the `.cmd` card (no `-n` CLI override for this binary) |
| A different generator sample | Point `Beams:LHEF` at it; add `ResonanceDecayFilter`/`POWHEG:*` blocks if it needs forced decays or is NLO-matched |
| A different detector/scenario | `export DELPHES_CARD=<full path>` — alternatives under `$DELPHES_DIR/cards/` |
| A different key4hep release | `export KEY4HEP_SETUP="<setup.sh> <options>"` |
| Which collections are written | Copy `$K4SIMDELPHES/edm4hep_output_config.tcl`, edit, pass as 2nd arg |
| Classic Delphes ROOT tree instead of EDM4hep | Use `DelphesPythia8` (3 args) instead |

---

## Stage 2: `condor_submit.py` — all fragments on HTCondor (lxplus)

One job per LHE fragment in `condor/fragments.txt`, each running
`gen/run_fragment.sh` (stage 1) on its fragment. `condor_submit.py -f <folder>`
creates `condor/<folder>/` with:

- `run_fragment.sh` — a short wrapper that sets this submission's options
  (output directory, `--delphes-card`, `--key4hep-setup`) and calls
  `gen/run_fragment.sh`. The jobs run in this folder, so the per-fragment
  `pythia_*.cmd` cards end up here too.
- `submit.sub` — memory starts at 2 GB and is raised automatically if a job
  is held for exceeding it; jobs stuck for > 2h at < 5% CPU are held and
  released; up to 2 retries; `+JobFlavour = "workday"` (~20-25 min/job actual).
- `outputs/`, `errors/`, `logs/` — stdout, stderr and condor log, one file per
  fragment (`<fragment>.txt` / `.log`).

Output goes to `<output>/<fragment>.edm4hep.root`, by default
`/eos/home-a/alpleban/FCC/vbf_ww_lvlv/samples/mg_pp_vbf_ww_lvlv_5f_84TeV_TrackCov`
— inside the directory `analysis_config.py`'s `input_dir` points at. Use a new
`-o` for every new card/setup: fragments whose output file already exists are
skipped.

**Submit:**
```bash
python3 condor_submit.py -f run1 [-o OUTPUT_DIR] [-i FRAGMENT_LIST] [--delphes-card CARD] [--key4hep-setup "SETUP"] [--flavour FLAVOUR]
```
It asks for confirmation, then submits and runs `condor_q`. Submitting from
`/eos` needs CERN's EosSubmit schedds; the script sets that up itself (the
same two variables `module load lxbatch/eossubmit` sets), so no `module load`
is needed for the submission.

**Monitor** (`module load` *is* needed here, once per terminal, or `condor_q`
looks at the default schedds and doesn't see the jobs):
```bash
module load lxbatch/eossubmit
condor_q
tail -f condor/run1/logs/<fragment>.log
ls <OUTPUT_DIR> | wc -l
```

**Resubmit failed jobs:**
```bash
grep -l "Job FAILED" condor/run1/outputs/*.txt   # which ones
python3 condor_submit.py -f run1 --retry         # resubmits only those
```

| Want to... | Change this |
|---|---|
| Process a subset | `-i <list of LHE files>` |
| Your own output area | `-o <dir>`, then point `input_dir` in `analysis_config.py` at its parent |
| Job length | `--flavour` (`espresso`, `microcentury`, `longlunch`, `workday`, ...) |
| Other resource requests | `write` calls for `submit.sub` in `condor_submit.py` |
| Pythia8 settings | `gen/mg_pp_vbf_ww_lvlv_5f_84TeV.cmd` (shared with stage 1) |
| Merge into one file (optional — `fccanalysis` reads a directory natively) | `hadd merged.edm4hep.root <OUTPUT_DIR>/*.root` |

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

Two processes are configured, from the same LHE events with different
detector cards, and overlaid in the plots (red / blue):

| Process (sample folder under `input_dir`) | Delphes card |
|---|---|
| `mg_pp_vbf_ww_lvlv_5f_84TeV` | `FCChh_II.tcl` |
| `mg_pp_vbf_ww_lvlv_5f_84TeV_TrackCov` | `FCChhTrackCov_II.tcl` |

Remove one from `process_list` in `analysis_config.py` if its samples are not
produced yet.

**Gotchas:**
- **Use key4hep `-r 2024-10-03`, not `-r 2026-04-08`** (nor the nightly used
  for the Delphes step) — this FCCAnalyses
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
