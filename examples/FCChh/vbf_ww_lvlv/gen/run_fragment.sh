#!/bin/bash
# Runs DelphesPythia8_EDM4HEP (Pythia8 shower + Delphes FCC-hh scenario II
# fast-sim) on one LHE fragment of mg_pp_vbf_ww_lvlv_5f_84TeV.
#
# Usage: ./run_fragment.sh <lhe_file> [output_dir] [n_events] [skip_events]
#   writes <output_dir>/<fragment>.edm4hep.root (output_dir defaults to the cwd)
#   and the fragment's Pythia8 card pythia_<fragment>.cmd in the cwd.
#   With n_events, only that many events are processed, after skipping the
#   first skip_events (default 0) of the LHE file, and <fragment> becomes
#   <fragment>_s<skip_events> - so one fragment can be split across jobs.
#   The output is first written as the hidden file .<fragment>.edm4hep.root
#   (skipped by the *.root globs of the analysis) and renamed when the job
#   succeeds, so a killed job never leaves a file that a resubmission would skip.
# Environment overrides:
#   DELPHES_CARD   (default: FCChhTrackCov_II.tcl)
#   KEY4HEP_SETUP  (default: "/cvmfs/sw-nightlies.hsf.org/key4hep/setup.sh --spack -r 2026-10-20")
# Prints "Job FINISHED" or "Job FAILED" (condor_submit.py --retry looks for these).
#
# NOTE: no "-u" here - the key4hep setup.sh references an unset variable
# internally and aborts under `set -u`.
set -eo pipefail
trap 'echo "Job FAILED"' ERR

if [ -z "$1" ]; then
    echo "Usage: $0 <lhe_file> [output_dir] [n_events] [skip_events]"
    exit 1
fi

LHE_FILE=$(realpath -m "$1")
OUTPUT_DIR=$(realpath -m "${2:-.}")
N_EVENTS="$3"
SKIP_EVENTS="${4:-0}"
FRAGMENT_NAME=$(basename "${LHE_FILE}" .lhe.gz)   # e.g. events_001453574
if [ -n "${N_EVENTS}" ]; then
    FRAGMENT_NAME="${FRAGMENT_NAME}_s${SKIP_EVENTS}"   # e.g. events_001453574_s2000
fi
OUTPUT_FILE="${OUTPUT_DIR}/${FRAGMENT_NAME}.edm4hep.root"
TMP_FILE="${OUTPUT_DIR}/.${FRAGMENT_NAME}.edm4hep.root"   # podio needs the .root extension
CARD_TEMPLATE="$(dirname "$(realpath "$0")")/mg_pp_vbf_ww_lvlv_5f_84TeV.cmd"

# DelphesPythia8_EDM4HEP exits 0 (and writes an output file) even if the LHE file is missing
if [ ! -f "${LHE_FILE}" ]; then
    echo "LHE file not found: ${LHE_FILE}"
    echo "Job FAILED"
    exit 1
fi

# Skip fragments already processed, so a resubmission doesn't redo finished work
if [ -f "${OUTPUT_FILE}" ]; then
    echo "Output already exists, skipping: ${OUTPUT_FILE}"
    echo "Job FINISHED"
    exit 0
fi

# Default is a date-pinned nightly: FCChhTrackCov_II.tcl aborts on the stable
# 2026-04-08 release (Delphes Kalman covariance instability, fixed upstream
# 2026-05-11). Spack nightlies are being retired, so override KEY4HEP_SETUP
# (e.g. with a newer stable release) once this one stops working.
KEY4HEP_SETUP="${KEY4HEP_SETUP:-/cvmfs/sw-nightlies.hsf.org/key4hep/setup.sh --spack -r 2026-10-20}"
# unquoted on purpose: the variable holds the script path plus its options.
# `set --` first: a sourced script without arguments of its own would
# otherwise see this script's $1 (the LHE file) as a setup.sh option.
set --
source ${KEY4HEP_SETUP}
DELPHES_CARD="${DELPHES_CARD:-${DELPHES_DIR}/cards/FCC/scenarios/FCChhTrackCov_II.tcl}"

# This fragment's Pythia8 card: the shared one with its Beams:* block replaced
CARD="pythia_${FRAGMENT_NAME}.cmd"
grep -v '^Beams:' "${CARD_TEMPLATE}" > "${CARD}"
{
    echo "Beams:frameType = 4"
    echo "Beams:setProductionScalesFromLHEF = off"
    echo "Beams:LHEF = ${LHE_FILE}"
} >> "${CARD}"
if [ -n "${N_EVENTS}" ]; then
    sed -i '/^Main:numberOfEvents/d' "${CARD}"
    {
        echo "Main:numberOfEvents = ${N_EVENTS}"
        echo "Beams:nSkipLHEFatInit = ${SKIP_EVENTS}"
    } >> "${CARD}"
fi

mkdir -p "${OUTPUT_DIR}"
# DelphesPythia8_EDM4HEP refuses to overwrite an existing output file (e.g. from a killed job)
rm -f "${TMP_FILE}"

DelphesPythia8_EDM4HEP \
    "${DELPHES_CARD}" \
    "${K4SIMDELPHES}/edm4hep_output_config.tcl" \
    "${CARD}" \
    "${TMP_FILE}"
mv "${TMP_FILE}" "${OUTPUT_FILE}"

echo "Wrote ${OUTPUT_FILE}"
echo "Job FINISHED"
