#!/bin/bash
# Runs DelphesPythia8_EDM4HEP on one LHE fragment of mg_pp_vbf_ww_lvlv_5f_84TeV.
# Usage: ./run_fragment.sh <path to events_<seed>.lhe.gz>
#
# Environment overrides (passed through by submit.sub):
#   OUTPUT_DIR  where the .edm4hep.root files go
#               (default: /eos/home-a/alpleban/FCC/vbf_ww_lvlv/samples/mg_pp_vbf_ww_lvlv_5f_84TeV)
#   CONDOR_DIR  this directory (default: the job's cwd, which on the EOS
#               schedds is the submission directory)
#
# NOTE: no "-u" here - /cvmfs/sw.hsf.org/key4hep/setup.sh itself references
# an unset variable internally and aborts under `set -u`.
set -eo pipefail

LHE_FILE="$1"
FRAGMENT_NAME=$(basename "${LHE_FILE}" .lhe.gz)   # e.g. events_001453574

CONDOR_DIR="${CONDOR_DIR:-$PWD}"
OUTPUT_DIR="${OUTPUT_DIR:-/eos/home-a/alpleban/FCC/vbf_ww_lvlv/samples/mg_pp_vbf_ww_lvlv_5f_84TeV}"
OUTPUT_FILE="${OUTPUT_DIR}/${FRAGMENT_NAME}.edm4hep.root"
CARD_TEMPLATE="${CONDOR_DIR}/../gen/mg_pp_vbf_ww_lvlv_5f_84TeV.cmd"

# Skip fragments already processed - lets you resubmit the whole fragment
# list after a partial failure without redoing finished work.
if [ -f "${OUTPUT_FILE}" ]; then
    echo "Output already exists, skipping: ${OUTPUT_FILE}"
    exit 0
fi

source /cvmfs/sw.hsf.org/key4hep/setup.sh -r 2026-04-08

# Build this fragment's Pythia8 card from the shared one in gen/, replacing
# its Beams:* block. NOTE: these EOS schedds run the job's cwd as the
# submission directory itself (condor/), not a throwaway scratch dir - so
# this small card file lands in condor/ too. The big .root output is written
# straight to OUTPUT_FILE below to avoid the same thing happening to it.
CARD="pythia_${FRAGMENT_NAME}.cmd"
grep -v '^Beams:' "${CARD_TEMPLATE}" > "${CARD}"
{
    echo "Beams:frameType = 4"
    echo "Beams:setProductionScalesFromLHEF = off"
    echo "Beams:LHEF = ${LHE_FILE}"
} >> "${CARD}"

mkdir -p "${OUTPUT_DIR}"

DelphesPythia8_EDM4HEP \
    "${DELPHES_DIR}/cards/FCC/scenarios/FCChh_II.tcl" \
    "${K4SIMDELPHES}/edm4hep_output_config.tcl" \
    "${CARD}" \
    "${OUTPUT_FILE}"

echo "Wrote ${OUTPUT_FILE}"
echo "Job FINISHED."
