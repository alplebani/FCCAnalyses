#!/bin/bash
# Generates minimum-bias pp events at 84 TeV with Pythia8 (through Delphes'
# converter card, i.e. no detector simulation) and converts them to the
# Delphes pile-up format read by the PileUpMerger in FCChh_II_PileUp.tcl.
#
# Usage: ./run_minbias.sh <seed> [n_events] [output_dir]
#   writes <output_dir>/MinBias_<seed>.pileup (n_events defaults to 10000,
#   output_dir to the cwd) and the job's Pythia8 card pythia_minbias_<seed>.cmd
#   in the cwd. Use a different seed for every job.
# Environment overrides:
#   KEY4HEP_SETUP  (default: "/cvmfs/sw-nightlies.hsf.org/key4hep/setup.sh --spack -r 2026-10-20")
# Prints "Job FINISHED" or "Job FAILED".
#
# NOTE: no "-u" here - the key4hep setup.sh references an unset variable
# internally and aborts under `set -u`.
set -eo pipefail
trap 'echo "Job FAILED"' ERR

if [ -z "$1" ]; then
    echo "Usage: $0 <seed> [n_events] [output_dir]"
    exit 1
fi

SEED="$1"
N_EVENTS="${2:-10000}"
OUTPUT_DIR=$(realpath -m "${3:-.}")
ROOT_FILE="${OUTPUT_DIR}/MinBias_${SEED}.root"
PILEUP_FILE="${OUTPUT_DIR}/MinBias_${SEED}.pileup"
CARD_TEMPLATE="$(dirname "$(realpath "$0")")/minbias_84TeV.cmd"

# Skip seeds already processed, so a resubmission doesn't redo finished work
if [ -f "${PILEUP_FILE}" ]; then
    echo "Output already exists, skipping: ${PILEUP_FILE}"
    echo "Job FINISHED"
    exit 0
fi

KEY4HEP_SETUP="${KEY4HEP_SETUP:-/cvmfs/sw-nightlies.hsf.org/key4hep/setup.sh --spack -r 2026-10-20}"
# unquoted on purpose: the variable holds the script path plus its options.
# `set --` first: a sourced script without arguments of its own would
# otherwise see this script's $1 (the seed) as a setup.sh option.
set --
source ${KEY4HEP_SETUP}

# This job's Pythia8 card: the shared one with its event count and seed replaced
CARD="pythia_minbias_${SEED}.cmd"
grep -v -e '^Main:numberOfEvents' -e '^Random:' "${CARD_TEMPLATE}" > "${CARD}"
{
    echo "Main:numberOfEvents = ${N_EVENTS}"
    echo "Random:setSeed = on"
    echo "Random:seed = ${SEED}"
} >> "${CARD}"

mkdir -p "${OUTPUT_DIR}"
# DelphesPythia8 refuses to overwrite an existing output file (e.g. from a killed job)
rm -f "${ROOT_FILE}"

DelphesPythia8 "${DELPHES_DIR}/cards/converter_card.tcl" "${CARD}" "${ROOT_FILE}"
root2pileup "${PILEUP_FILE}" "${ROOT_FILE}"
rm -f "${ROOT_FILE}"

echo "Wrote ${PILEUP_FILE}"
echo "Job FINISHED"
