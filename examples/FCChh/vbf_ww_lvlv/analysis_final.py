'''
Final-selection / cutflow stage for FCC-hh VBF WW -> lvlv.
Adapted from examples/FCChh/vbf_hww/analysis_final.py (VBF H->WW), with the
Higgs-specific MT/lep_cent cuts dropped (those used AnalysisFCChh helper
functions that don't exist in this FCCAnalyses build - see analysis_stage1.py).
'''
import vbf_ww_lvlv.analysis_config as analysis_config

inputDir = analysis_config.stage1_output
outputDir = analysis_config.final_output

processList = {}
for proc in analysis_config.process_list:
    processList[proc] = {}

# Central cross-section dictionary (fallback lookup for any process not
# covered by procDictAdd below - our process isn't in it, but fccanalysis
# requires this variable to point at a readable file regardless).
procDict = '/eos/experiment/fcc/hh/utils/FCCDicts/FCChh_procDict_fcc_v07_II.json'

# Cross section for mg_pp_vbf_ww_lvlv_5f_84TeV: read off the "Integrated
# weight (pb)" line Pythia8 prints from the LHEF header when showering any
# fragment of this sample (same physical process/run_card for every
# fragment, so the same cross section applies regardless of which/how many
# fragments you've actually processed - confirmed identical on two
# independently-run fragments).
# numberOfEvents/sumOfWeights are placeholders - fccanalysis overwrites them
# with the true values read back from the stage1 output for this sample.
procDictAdd = {
    'mg_pp_vbf_ww_lvlv_5f_84TeV': {
        'numberOfEvents': 10000, 'sumOfWeights': 10000,
        'crossSection': 11.8889861497, 'kfactor': 1.0, 'matchingEfficiency': 1.0,
    },
}

# Expected integrated luminosity (FCC-hh baseline), in pb-1
intLumi = 30e+06

# Whether to scale to expected integrated luminosity
doScale = True

# Number of CPUs to use
nCPUS = 2

# produces ROOT TTrees, default is False
doTree = True

saveTabular = True

# Use weighted events (this LO, unweighted sample has weight==1 throughout,
# kept here for forward-compatibility with any weighted sample added later)
do_weighted = False

# Define new variables
defineList = {
    'n_lep': 'n_el+n_mu',
}

# Dictionary of the list of cuts. The key is the name of the selection that
# will be added to the output file.
cutList = {}
cutList['sel0_all'] = '1.0'
cutList['sel1_bjeteveto'] = 'n_bjets_loose==0'
cutList['sel2_jeteveto'] = 'n_jets==2'
cutList['sel3_both'] = cutList['sel1_bjeteveto'] + ' && ' + cutList['sel2_jeteveto']
cutList['sel4_mjj'] = cutList['sel3_both'] + ' && (m_jj[0]>500.0) && (deta_jj[0]>4.0)'
cutList['sel5_mem'] = cutList['sel3_both'] + ' && (m_em[0]<70.0)'

# Dictionary for the output variable/histograms. "name" = branch name in the
# input file, "title" = x-axis label, "bin"/"xmin"/"xmax" the binning.
histoList = {
    'n_jets': {'title': 'Number of jets', 'bin': 10, 'xmin': 0, 'xmax': 10},
    'n_centraljets': {'title': 'Number of central jets (|#eta|<2.5)', 'bin': 10, 'xmin': 0, 'xmax': 10},
    'n_bjets': {'title': 'Number of medium b-jets', 'bin': 10, 'xmin': 0, 'xmax': 10},
    'n_bjets_loose': {'title': 'Number of loose b-jets', 'bin': 10, 'xmin': 0, 'xmax': 10},
    'j1_pt': {'title': 'Leading jet p_{T} [GeV]', 'bin': 100, 'xmin': 0, 'xmax': 500},
    'j1_eta': {'title': 'Leading jet #eta', 'bin': 100, 'xmin': -10, 'xmax': 10},
    'j2_pt': {'title': 'Subleading jet p_{T} [GeV]', 'bin': 100, 'xmin': 0, 'xmax': 500},
    'j2_eta': {'title': 'Subleading jet #eta', 'bin': 100, 'xmin': -10, 'xmax': 10},
    'pt_jj': {'title': 'Di-jet p_{T} [GeV]', 'bin': 100, 'xmin': 0, 'xmax': 500},
    'm_jj': {'title': 'm_{jj} [GeV]', 'bin': 40, 'xmin': 0, 'xmax': 10000},
    'dphi_jj': {'title': '#Delta#phi_{jj}', 'bin': 30, 'xmin': 0, 'xmax': 3.1416},
    'deta_jj': {'title': '#Delta#eta_{jj}', 'bin': 120, 'xmin': 0, 'xmax': 12.0},
    'el1_pt': {'title': 'Leading electron p_{T} [GeV]', 'bin': 40, 'xmin': 0, 'xmax': 200},
    'mu1_pt': {'title': 'Leading muon p_{T} [GeV]', 'bin': 40, 'xmin': 0, 'xmax': 200},
    'm_em': {'title': 'm_{e#mu} [GeV]', 'bin': 60, 'xmin': 0, 'xmax': 300},
    'dphi_em': {'title': '#Delta#phi_{e#mu}', 'bin': 30, 'xmin': 0, 'xmax': 3.1416},
    'deta_em': {'title': '#Delta#eta_{e#mu}', 'bin': 12, 'xmin': 0, 'xmax': 12.0},
    'dphi_emMET': {'title': '#Delta#phi(e#mu,MET)', 'bin': 30, 'xmin': 0, 'xmax': 3.1416},
    'MET': {'title': 'Missing E_{T} [GeV]', 'bin': 40, 'xmin': 0, 'xmax': 1000},
}

for key, val in histoList.items():
    if 'name' not in val:
        val['name'] = key
