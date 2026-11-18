# VBF W+W- → eμνν with pile-up (`FCChh_II_PileUp.tcl`)

How to produce `mg_pp_vbf_ww_lvlv_5f_84TeV` with pile-up (⟨μ⟩ = 200) on top
of the FCC-hh scenario II Delphes card. Status: the card and scripts are tested
on single events; the full production has **not** been run yet (it needs ~2 TB,
see [Size and time](#size-and-time)).

## Files

All in `gen/`:

| File | What it is |
|---|---|
| `minbias_84TeV.cmd` | Pythia8 card: min-bias pp at 84 TeV (`SoftQCD:all = on`, default tune) |
| `run_minbias.sh` | Generates min-bias events and converts them to Delphes' `.pileup` format |
| `FCChh_II_PileUp.tcl` | Copy of `cards/FCC/scenarios/FCChh_II.tcl` with pile-up added |
| `track/electron/muonMomentumResolution_II.tcl`, `dzResolutionVsP.tcl` | Files `source`d by the card - must stay next to it |
| `run_fragment.sh` | Pythia8 + Delphes on one LHE fragment, optionally only part of it |

`condor_submit.py` (one level up) submits `run_fragment.sh` to Condor.

## Environment

Both scripts source key4hep themselves, so run them from a fresh shell.
Default: `/cvmfs/sw-nightlies.hsf.org/key4hep/setup.sh --spack -r 2026-10-20`.
Override with `export KEY4HEP_SETUP="<setup.sh path + options>"`.

The nightly is needed because the Delphes in the stable 2026-04-08 release
crashes with the TrackCov card. The pile-up card itself is based on plain `FCChh_II`.

## 1. Min-bias file

`PileUpMerger` adds Poisson(⟨μ⟩) events drawn at random from a pre-generated
file of min-bias collisions. Delphes doesn't ship one at 84 TeV (docs:
<https://delphes.github.io/workbook/pile-up>).

```bash
./gen/run_minbias.sh <seed> [n_events=10000] [output_dir=.]
# -> <output_dir>/MinBias_<seed>.pileup
```

This runs `DelphesPythia8` with `cards/converter_card.tcl` (no detector), then
`root2pileup`. Notes:

- ~7.7 kB per event. The existing file `/eos/user/a/alpleban/FCC/Samples/MinBias/MinBias_1.pileup`
  is 967 MB, i.e. ~125k events.
- `PileUpMerger` reads **one** file, and `.pileup` files can't be merged with `cat`.
  For a bigger pool, `hadd` the intermediate ROOT files and run `root2pileup` once
  (the script currently deletes the ROOT file - remove that line).
- At ⟨μ⟩ = 200 each signal event uses ~200 min-bias events, so a small pool is
  reused many times. 10⁵-10⁶ events is a reasonable size.

## 2. Pile-up card

Changes in `FCChh_II_PileUp.tcl` relative to `FCChh_II.tcl`:

1. `PileUpMerger` first in the `ExecutionPath`, with its module block
   (taken from `cards/FCC/FCChh_PileUp.tcl`):
   - `PileUpFile` - **full path** to the `.pileup` file (line ~132). **Change this on a new machine.**
   - `MeanPileUp 200` (HL-LHC value; FCC-hh baseline is ~1000)
   - `ZVertexSpread`, `TVertexSpread`, `VertexDistributionFormula`
2. `ParticlePropagator` reads `PileUpMerger/stableParticles` instead of
   `Delphes/stableParticles`. `NeutrinoFilter` stays on `Delphes/stableParticles`,
   so the generator-level MET comes from the hard event only.
3. Charged pile-up subtraction: `TrackPileUpSubtractor` right after `TrackMerger`,
   reading `TrackMerger/tracks` and `PileUpMerger/vertices`. Everything that used
   `TrackMerger/tracks` (`ForwardLooperTracks`, `Calorimeter`, the b-tagging
   modules) now reads `TrackPileUpSubtractor/tracks`.
4. `ForwardLooperTracks`: `UseMomentumVector false` (lowercase - newer Delphes
   rejects `False`).

There is no neutral pile-up subtraction (PUPPI / `JetPileUpSubtractor`), so jets
and MET are strongly affected (~170 jets per event before cuts).

**Gotcha:** Delphes resolves `source` paths relative to the card's directory,
even absolute ones. That's why the resolution files are copied next to the card.
Move them together.

## 3. Single-fragment test

```bash
export DELPHES_CARD=$PWD/gen/FCChh_II_PileUp.tcl
./gen/run_fragment.sh <lhe_file> <test_dir> 2 0     # 2 events, skip 0
```

Arguments are `<lhe_file> [output_dir] [n_events] [skip_events]`:

- With `n_events`, only that many events are processed, after skipping
  `skip_events` (Pythia's `Beams:nSkipLHEFatInit`), and the output is called
  `<fragment>_s<skip>.edm4hep.root`.
- The output is written as a hidden `.<name>.edm4hep.root` and renamed on success.
  A killed job therefore leaves no file that a rerun would skip, and the analysis
  `*.root` globs ignore it. (podio needs the `.root` extension, so a `.part`
  suffix doesn't work.)
- Existing outputs are skipped. Delete them to rerun.

## 4. Condor production

```bash
python3 condor_submit.py -f run_pu \
    -o <output_dir>/mg_pp_vbf_ww_lvlv_5f_84TeV_PU200 \
    --delphes-card $PWD/gen/FCChh_II_PileUp.tcl \
    --events-per-job 2000 --flavour tomorrow \
    [-i <list_of_lhe_files>]
```

- `--events-per-job 2000` splits each 10k-event fragment into 5 jobs
  (`--events-per-fragment`, default 10000, sets the fragment size).
- `--retry` (with the same options) resubmits every job whose stdout lacks
  "Job FINISHED", including jobs Condor killed for wall time.
- **CERN-specific:** submission files on `/eos` go to the EOS-submit scheduler.
  To see the jobs, `condor_q` needs `module load lxbatch/eossubmit` (or
  `export _myschedd_POOL=eossubmit _condor_CONDOR_HOST='tweetybird04.cern.ch, tweetybird03.cern.ch'`).
  Stdout and error files only appear once a job starts. On a non-CERN cluster,
  adapt the `eos_env` part of `condor_submit.py` and the `+JobFlavour` / `MY.WantOS` lines.

## Size and time

Measured with ⟨μ⟩ = 200:

| | No pile-up | ⟨μ⟩ = 200 |
|---|---|---|
| Time per event | fast | ~11 s |
| Size per event | ~180 kB | ~2.2 MB |
| Tracks / neutral hadrons / jets per event | ~280 / ~60 / ~4 | ~2000 / ~9000-16000 / ~170 |
| Full sample (100 fragments × 10k events) | 171 GB | **~2.1 TB** |

- 10k events per job (`workday`, 8 h) got killed after ~2600 events. With
  2000 events per job, expect ~6 h per job.
- The size comes mostly from `ReconstructedParticles` and the EFlow collections
  (~60%), which stage 1 needs. The hit collections (~20%) are written by
  k4SimDelphes and can't be dropped from the output config.

Ways to fit the disk space:

1. Run stage 1 in the same job and delete the EDM4HEP file afterwards (not implemented yet).
2. Fewer fragments via `-i` (~22 GB per fragment).
3. Lower `MeanPileUp` (size scales roughly linearly).

## 5. Analysis

1. Add `'mg_pp_vbf_ww_lvlv_5f_84TeV_PU200'` to `process_list` in `analysis_config.py`.
2. Add matching `plots` / `colors` / `legend` entries in `analysis_plots.py`
   (the plot style comes from `python/do_plots.py`).
3. Run stage 1 → final → plots as for the other samples.
