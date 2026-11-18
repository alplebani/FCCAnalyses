# Handoff: vbf_ww_lvlv (written 2026-10-28 evening)

Repo: `/eos/home-a/alpleban/FCC/FCCAnalyses`, branch `pileup`, example in
`examples/FCChh/vbf_ww_lvlv/`. Nothing from this work is committed yet
(user commits themself — don't commit unless asked). Overview of the
workflow: `README.md` in this folder.

## Where things stand

**Condor production running:** cluster `1536039`, batch name `vbf_ww_lvlv_run1`,
100 jobs (one per LHE fragment), submitted 2026-10-28 ~18:30 with
`python3 condor_submit.py -f run1` (default settings: `FCChhTrackCov_II.tcl`,
key4hep nightly `--spack -r 2026-10-20`). At 18:34: 37 running, 63 idle.

- Output: `/eos/home-a/alpleban/FCC/vbf_ww_lvlv/samples/mg_pp_vbf_ww_lvlv_5f_84TeV_TrackCov/<fragment>.edm4hep.root`
- Job stdout/stderr/logs: `condor/run1/{outputs,errors,logs}/<fragment>.txt|.log`
- Expected ~20-25 min/job.

**First thing to do tomorrow — check the production:**
```bash
cd /eos/home-a/alpleban/FCC/FCCAnalyses/examples/FCChh/vbf_ww_lvlv
module load lxbatch/eossubmit            # needed for manual condor_q (the script sets it itself)
condor_q
grep -L "Job FINISHED" condor/run1/outputs/*.txt   # jobs that didn't finish
grep -l "Job FAILED"   condor/run1/outputs/*.txt
ls /eos/home-a/alpleban/FCC/vbf_ww_lvlv/samples/mg_pp_vbf_ww_lvlv_5f_84TeV_TrackCov | wc -l   # want 100
```
From Claude's Bash tool, instead of `module load` prefix commands with
`_myschedd_POOL=eossubmit _condor_CONDOR_HOST="tweetybird04.cern.ch, tweetybird03.cern.ch"`.

**Known risk — partial outputs:** `DelphesPythia8_EDM4HEP` creates the output
file when the job *starts* (37 files existed with 37 jobs running). The job
script skips fragments whose output file exists, so a job that was killed or
evicted mid-run leaves a truncated file and a resubmit/`--retry` would skip it
instead of redoing it. Before trusting the sample: for every fragment without
"Job FINISHED" in `outputs/`, delete its `.edm4hep.root`, then
`python3 condor_submit.py -f run1 --retry` (note `--retry` only picks up
"Job FAILED", not evicted/killed jobs with no message). Possible fix to
discuss with the user: write to a temp name and `mv` at the end in
`gen/run_fragment.sh`.

Note: run1's jobs use an older, self-contained `condor/run1/run_fragment.sh`
(generated before the refactor below). Any new submission gets the thin
wrapper version.

## Then: analysis (stage 3)
Once 100 TrackCov files are there, run the fccanalysis chain (README "Stage 3";
key4hep `-r 2024-10-03`, `PYTHONPATH=$PWD/examples/FCChh`). `analysis_config.py`
overlays two processes: `mg_pp_vbf_ww_lvlv_5f_84TeV` (FCChh_II card, already
produced) and `mg_pp_vbf_ww_lvlv_5f_84TeV_TrackCov` (this production).

## What changed today (uncommitted)
- `condor_submit.py` (new, lxplus): modelled on the user's
  `/eos/user/a/alpleban/Diboson/Analysis/source/WZanalysisFramework/NtupleAnalysis/Cam_condor_submit.py`.
  `-f <folder>` → creates `condor/<folder>/` with `run_fragment.sh` (wrapper
  calling `gen/run_fragment.sh`), `submit.sub`, `outputs/ errors/ logs/`;
  confirmation prompt; submits via `subprocess.run` with the EosSubmit env
  vars; `--retry`, `-o`, `-i`, `--delphes-card`, `--key4hep-setup`, `--flavour`.
- `gen/run_fragment.sh` (new): general single-fragment runner,
  `./gen/run_fragment.sh <lhe_file> [output_dir]`; env overrides
  `DELPHES_CARD`, `KEY4HEP_SETUP`; checks LHE exists, skips existing output,
  prints "Job FINISHED"/"Job FAILED".
- Deleted: `condor/run_fragment.sh`, `condor/submit.sub` (replaced by the above).
- `condor/fragments.txt` recreated (identical to the committed one).
- `README.md` rewritten for the new workflow; `.gitignore` now ignores
  `condor/*/` and `pythia_events_*.cmd`.
- Earlier, unrelated uncommitted edits in `analysis_config.py`,
  `analysis_final.py`, `analysis_plots.py`, `gen/run_delphes_pythia8.sh` and
  new `README_TrackCov.md` — the user's own, leave alone unless asked.

## Open items
- `README_TrackCov.md` still describes the old workflow (`export OUTPUT_DIR`,
  `condor/run_fragment.sh`, `condor_submit submit.sub`) — offered to update.
- `gen/run_delphes_pythia8.sh` is now redundant with `gen/run_fragment.sh` —
  offered to remove; user hasn't decided.
- `condor/run1/run_job.sh` is a leftover from a failed first submission, unused.

## lxplus gotchas learned today
- `stream_output`/`stream_error` are rejected by the lxplus schedds (since Nov 2025).
- Submitting from `/eos` needs the EosSubmit schedds; `module load
  lxbatch/eossubmit` only sets `_myschedd_POOL=eossubmit` and
  `_condor_CONDOR_HOST=tweetybird04.cern.ch, tweetybird03.cern.ch`.
  A script can't load it into the user's shell.
- `DelphesPythia8_EDM4HEP` exits 0 and writes an output file even if the LHE
  input doesn't exist.
- `FCChhTrackCov_II.tcl` needs the 2026-10-20 nightly (aborts on stable 2026-04-08).

## User preferences (also in ~/.claude/CLAUDE.md)
python3; short explanations; no commits unless asked; ask before background
runs; Python scripts: no top-of-file docstring, no globals — variables in
`if __name__ == '__main__':` passed to functions.
