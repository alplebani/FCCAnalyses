#!/bin/bash
# Single-step Delphes run: Pythia8 showers the LHE file (per the .cmd card's
# Beams:LHEF setting) and Delphes runs the FCC-hh scenario II fast-sim on
# the result, writing EDM4hep output directly - no Gaudi/k4run needed.
#
# Usage: ./run_delphes_pythia8.sh [output_file]
#   output_file defaults to mg_pp_vbf_ww_lvlv_5f_84TeV_delphes_scenII_TrackCov.edm4hep.root
#   next to this script.
# Environment overrides:
#   DELPHES_CARD   (default: FCChhTrackCov_II.tcl)
#   KEY4HEP_SETUP  (default: "/cvmfs/sw-nightlies.hsf.org/key4hep/setup.sh --spack -r 2026-10-20")
# NOTE: no "-u" here - /cvmfs/sw.hsf.org/key4hep/setup.sh itself references
# an unset variable internally and fails under `set -u`.
set -eo pipefail

OUTPUT_FILE=$(realpath -m "${1:-$(dirname "$0")/mg_pp_vbf_ww_lvlv_5f_84TeV_delphes_scenII_TrackCov.edm4hep.root}")
cd "$(dirname "$0")"

# Default is a date-pinned nightly: FCChhTrackCov_II.tcl aborts on the stable
# 2026-04-08 release (Delphes Kalman covariance instability, fixed upstream
# 2026-05-11). Spack nightlies are being retired, so override KEY4HEP_SETUP
# (e.g. with a newer stable release) once this one stops working.
KEY4HEP_SETUP="${KEY4HEP_SETUP:-/cvmfs/sw-nightlies.hsf.org/key4hep/setup.sh --spack -r 2026-10-20}"
# unquoted on purpose: the variable holds the script path plus its options.
# `set --` first: a sourced script without arguments of its own would
# otherwise see this script's $1 (the output file) as a setup.sh option.
set --
source ${KEY4HEP_SETUP}
DELPHES_CARD="${DELPHES_CARD:-$DELPHES_DIR/cards/FCC/scenarios/FCChhTrackCov_II.tcl}"

DelphesPythia8_EDM4HEP \
    "${DELPHES_CARD}" \
    "$K4SIMDELPHES/edm4hep_output_config.tcl" \
    mg_pp_vbf_ww_lvlv_5f_84TeV.cmd \
    "${OUTPUT_FILE}"
