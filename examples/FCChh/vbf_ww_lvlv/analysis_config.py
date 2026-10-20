# This propagates config from one stage to the next.
# Modeled on examples/FCChh/vbf_hww/analysis_config.py.

# Mandatory: list of processes to run over. Key = process name, which must
# match either <input_dir>/<name>.root (single file) or <input_dir>/<name>/
# (directory of .root files - used here, since the Delphes production on
# Condor writes one file per LHE fragment into this directory).
fraction = 1.0

process_list = {
    'mg_pp_vbf_ww_lvlv_5f_84TeV': {'fraction': fraction},
}

# Directory containing one subdirectory per process (see above). Condor jobs
# in ../../condor/ write their output here.
input_dir = '/eos/user/a/alpleban/FCC/vbf_ww_lvlv/samples'

# NOTE: trailing slashes are required - do_plots.py builds paths with plain
# string concatenation (inputDir + filename), not os.path.join.
stage1_output = '/eos/user/a/alpleban/FCC/vbf_ww_lvlv/outputs/stage1/'
final_output = '/eos/user/a/alpleban/FCC/vbf_ww_lvlv/outputs/final/'
plots_output = '/eos/user/a/alpleban/FCC/vbf_ww_lvlv/outputs/plots/'
