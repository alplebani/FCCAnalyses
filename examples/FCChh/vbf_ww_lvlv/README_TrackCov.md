# VBF W+W- → eμνν with the `FCChhTrackCov_II` Delphes card

How to produce and analyse `mg_pp_vbf_ww_lvlv_5f_84TeV` with the FCC-hh
scenario II **track-covariance** detector card,
[`FCChhTrackCov_II.tcl`](https://github.com/delphes/delphes/blob/master/cards/FCC/scenarios/FCChhTrackCov_II.tcl),
step by step. No pile-up.

For the general description of the folder, the Pythia8 card, the output
collections and the selection, see [`README.md`](README.md).

## What is different from the default `FCChh_II.tcl` setup

| | `FCChh_II.tcl` (original samples) | `FCChhTrackCov_II.tcl` (this README) |
|---|---|---|
| Track smearing | simple momentum smearing | full track-parameter covariance (`TrackCovariance` module) |
| key4hep for Pythia8 + Delphes | stable `2026-04-08` | nightly `2026-10-20` (see below) |
| Sample folder | `samples/mg_pp_vbf_ww_lvlv_5f_84TeV/` | `samples/mg_pp_vbf_ww_lvlv_5f_84TeV_TrackCov/` |
| Process name in the analysis | `mg_pp_vbf_ww_lvlv_5f_84TeV` | `mg_pp_vbf_ww_lvlv_5f_84TeV_TrackCov` |
| Pythia8 card, LHE files, selection | same | same |

The scripts in `gen/` and `condor/` already default to this card, this
key4hep setup and this sample folder — nothing needs to be exported for the
standard workflow below.

### Why a nightly key4hep

With the latest stable key4hep (`2026-04-08`) Delphes aborts on this card
after ~10 events:
```
SolTrack::KalmanCov: Error matrix not positive definite.
TrkUtil::CovSmear: covariance matrix has negative diagonal elements. Aborting.
 *** Break *** segmentation violation
```
This is a Delphes bug, fixed upstream on 2026-05-11 ("Set protection for
numerical instability in Kalman calculation of track parameter covariance
matrix"), that no stable release contains yet. The date-pinned nightly
`/cvmfs/sw-nightlies.hsf.org/key4hep/setup.sh --spack -r 2026-10-20` has the
fix; tested: no warnings, output readable by the FCCAnalyses step.

Key4hep is retiring the Spack nightlies (the setup prints *"The --spack
option will soon fail"*). When that happens, or once a stable release newer
than 2026-05-11 exists, override the setup instead of editing the scripts:
```bash
export KEY4HEP_SETUP="/cvmfs/sw.hsf.org/key4hep/setup.sh -r <newer-release>"
# or the rolling nightly (changes every week, not reproducible):
export KEY4HEP_SETUP="/cvmfs/sw-nightlies.hsf.org/key4hep/setup.sh"
```

### Settings you can override

Both `gen/run_delphes_pythia8.sh` and `condor/run_fragment.sh` read:

| Variable | Default |
|---|---|
| `DELPHES_CARD` | `$DELPHES_DIR/cards/FCC/scenarios/FCChhTrackCov_II.tcl` |
| `KEY4HEP_SETUP` | `/cvmfs/sw-nightlies.hsf.org/key4hep/setup.sh --spack -r 2026-10-20` |
| `OUTPUT_DIR` (condor only) | `/eos/home-a/alpleban/FCC/vbf_ww_lvlv/samples/mg_pp_vbf_ww_lvlv_5f_84TeV_TrackCov` |

`condor/submit.sub` forwards them to the jobs only if they are set in the
shell you submit from. `OUTPUT_DIR` defaults to the author's EOS area — set
your own (see step 3). If you set `DELPHES_CARD`, use a full path:
`$DELPHES_DIR` only exists after the setup script has run inside the job.

---

## Step 1 — running on a single file

Checks that Pythia8 + Delphes work with this card before using the batch
system: runs one whole LHE file (10000 events, ~20–25 min) locally. Fresh
shell on lxplus, from `condor/` (the script sets up key4hep itself):

```bash
cd examples/FCChh/vbf_ww_lvlv/condor
export OUTPUT_DIR=/eos/user/a/alpleban/vbf_ww_lvlv/samples/test_TrackCov
./run_fragment.sh /eos/experiment/fcc/hh/generation/lhe/mg_pp_vbf_ww_lvlv_5f_84TeV/events_001453574.lhe.gz
```
Output: `$OUTPUT_DIR/events_001453574.edm4hep.root`. Any line of
`fragments.txt` can be used as the input file.

**Check: plotting script to look at variables saved**
```bash
source /cvmfs/sw.hsf.org/key4hep/setup.sh -r 2026-04-08
python3 ../inspect_vbf_ww.py $OUTPUT_DIR/events_001453574.edm4hep.root   # plots in ./plots/
```


## Step 2 — all 100 fragments on HTCondor

Same shell (or redo `module load lxbatch/eossubmit` and `export OUTPUT_DIR=...`):
```bash
condor_submit submit.sub
```
100 jobs (`+JobFlavour = "workday"`, ~20–25 min each, ~1.5 GB output each,
so ~150 GB in total — check your EOS quota). The fragment from
step 2 is skipped automatically: `run_fragment.sh` exits immediately for any
fragment whose output file already exists.

**Monitor:**
```bash
condor_q
tail -f logs/<ClusterId>.log
ls $OUTPUT_DIR | wc -l                   # 100 when complete
```

**Resubmit failures:** just run `condor_submit submit.sub` again — finished
fragments are skipped, only missing ones are redone. To find which failed:
```bash
grep -L "Job FINISHED" logs/<ClusterId>.*.out
```

> Use a new `OUTPUT_DIR` whenever you change card or key4hep setup: because of
> the skip logic, pointing at a folder that already holds files from another
> setup silently reuses them.

## Step 3 — FCCAnalyses: stage1 → final → plots

Uses a **different** key4hep release from steps 1–3: this FCCAnalyses build
needs `-r 2024-10-03` (newer ROOT segfaults on startup). Fresh shell, from
the FCCAnalyses root:

```bash
cd /path/to/FCCAnalyses
source /cvmfs/sw.hsf.org/key4hep/setup.sh -r 2024-10-03
source ./setup.sh
export PYTHONPATH=$PWD/examples/FCChh:$PYTHONPATH
```

Before running, check `examples/FCChh/vbf_ww_lvlv/analysis_config.py`:
- `input_dir` must be the **parent** of your `OUTPUT_DIR` (the folder that
  contains `mg_pp_vbf_ww_lvlv_5f_84TeV_TrackCov/`),
- `process_list` contains both `mg_pp_vbf_ww_lvlv_5f_84TeV` (FCChh_II) and
  `mg_pp_vbf_ww_lvlv_5f_84TeV_TrackCov`. Comment out the FCChh_II one if you
  have not produced those samples,
- `stage1_output`, `final_output`, `plots_output` point to your own area
  (trailing `/` required).

Then:
```bash
fccanalysis run   examples/FCChh/vbf_ww_lvlv/analysis_stage1.py   # ntuples, one per process
fccanalysis final examples/FCChh/vbf_ww_lvlv/analysis_final.py    # cutflow + histograms
fccanalysis plots examples/FCChh/vbf_ww_lvlv/analysis_plots.py    # plots
```
Quick test of stage1 on a single file first, if you like:
```bash
fccanalysis run examples/FCChh/vbf_ww_lvlv/analysis_stage1.py \
    --files-list $OUTPUT_DIR/events_001453574.edm4hep.root --output test_stage1.root
```

## Step 4 — outputs

| Where | What |
|---|---|
| `<stage1_output>/mg_pp_vbf_ww_lvlv_5f_84TeV_TrackCov.root` | stage1 ntuple |
| `<final_output>/mg_pp_vbf_ww_lvlv_5f_84TeV_TrackCov_<selection>_histo.root` | histograms per selection stage |
| `<final_output>/mg_pp_vbf_ww_lvlv_5f_84TeV_TrackCov_<selection>.root` | event tree per selection stage (`doTree = True`) |
| `fccanalysis final` terminal output / LaTeX tables in `<final_output>` | cutflow (raw and scaled to 30 ab⁻¹) |
| `<plots_output>/<selection>/` | plots, FCChh_II (red) and FCChhTrackCov_II (blue) overlaid |

Both processes use the same cross-section (11.8889861497 pb, same LHE
events), so differences between the red and blue curves come only from the
detector card.

