#!/bin/bash
# Single-step Delphes run: Pythia8 showers the LHE file (per the .cmd card's
# Beams:LHEF setting) and Delphes runs the FCC-hh scenario II fast-sim on
# the result, writing EDM4hep output directly - no Gaudi/k4run needed.
#
# Usage: ./run_delphes_pythia8.sh [output_file]
#   output_file defaults to mg_pp_vbf_ww_lvlv_5f_84TeV_delphes_scenII.edm4hep.root
#   next to this script.
# NOTE: no "-u" here - /cvmfs/sw.hsf.org/key4hep/setup.sh itself references
# an unset variable internally and fails under `set -u`.
set -eo pipefail

OUTPUT_FILE=$(realpath -m "${1:-$(dirname "$0")/mg_pp_vbf_ww_lvlv_5f_84TeV_delphes_scenII.edm4hep.root}")
cd "$(dirname "$0")"

source /cvmfs/sw.hsf.org/key4hep/setup.sh -r 2026-04-08

DelphesPythia8_EDM4HEP \
    "$DELPHES_DIR/cards/FCC/scenarios/FCChh_II.tcl" \
    "$K4SIMDELPHES/edm4hep_output_config.tcl" \
    mg_pp_vbf_ww_lvlv_5f_84TeV.cmd \
    "${OUTPUT_FILE}"
