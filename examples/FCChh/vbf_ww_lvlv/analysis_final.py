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

# Define new variables.
# NOTE: deta_jj/deta_em/dphi_em from stage1 come from
# AnalysisFCChh::get_angularDist_pair, which (in this build) truncates dEta to
# an integer (unqualified abs() -> int abs(int)) and returns a *signed* dPhi
# for "dPhiAbs". They are recomputed here from the per-object eta/phi instead.
defineList = {
    'n_lep': 'n_el+n_mu',
    # m_em is empty if the e-mu pair is same-sign (getDFOSPairs) -> -1
    'm_ll': 'm_em.size() > 0 ? m_em[0] : -1.f',
    'lep1_pt': 'std::max(el1_pt, mu1_pt)',
    'lep2_pt': 'std::min(el1_pt, mu1_pt)',
    'deta_jj_abs': 'std::abs(j1_eta - j2_eta)',
    'dphi_jj_abs': 'std::abs(TVector2::Phi_mpi_pi(j1_phi - j2_phi))',
    'deta_em_abs': 'std::abs(el1_eta - mu1_eta)',
    'dphi_em_abs': 'std::abs(TVector2::Phi_mpi_pi(el1_phi - mu1_phi))',
    # ATLAS lepton centrality w.r.t. the two leading jets (arXiv:2403.04869, Eq. 1):
    # zeta = min(min(eta_l) - min(eta_j), max(eta_j) - max(eta_l))
    'zeta': 'std::min(std::min(el1_eta, mu1_eta) - std::min(j1_eta, j2_eta),'
            ' std::max(j1_eta, j2_eta) - std::max(el1_eta, mu1_eta))',
            
}

# Dictionary of the list of cuts. The key is the name of the selection that
# will be added to the output file.
# Cumulative selection following the ATLAS EW W+W-jj -> e mu nu nu signal
# region (arXiv:2403.04869, Table 1), plus its fiducial m_jj cut (Table 4):
# Object acceptances are kept at the stage1 (FCC-hh) values rather than
# ATLAS's: leptons and b-jets |eta| < 4, jets pT > 30 GeV (ATLAS: 25 GeV,
# |eta| < 4.5), b-jets pT > 20 GeV, loose WP (ATLAS: 85% WP, |eta| < 2.5).
#  - one e + one mu, opposite charge, pT > 27 GeV (3rd-lepton veto with
#    pT > 10 GeV already applied in stage1 via n_el == 1 && n_mu == 1)
#  - m_emu > 80 GeV: suppresses VBF H->WW
#  - MET > 15 GeV: Drell-Yan
#  - no loose b-jet: ttbar / tW
#  - exactly two jets (ATLAS 2-jet region, used for the comparison plots)
#  - lepton centrality zeta > 0.5
#  - m_jj > 500 GeV (ATLAS fiducial region; the SR itself uses an NN)
cutList = {}
cutList['sel0_all'] = '1.0'
cutList['sel1_lep'] = '(m_ll > 0) && (el1_pt > 27.) && (mu1_pt > 27.)'
cutList['sel2_mll'] = cutList['sel1_lep'] + ' && (m_ll > 80.)'
cutList['sel3_met'] = cutList['sel2_mll'] + ' && (MET[0] > 15.)'
cutList['sel4_bveto'] = cutList['sel3_met'] + ' && (n_bjets_loose == 0)'
cutList['sel5_njets'] = cutList['sel4_bveto'] + ' && (n_jets == 2)'
cutList['sel6_zeta'] = cutList['sel5_njets'] + ' && (zeta > 0.5)'
cutList['sel7_mjj'] = cutList['sel6_zeta'] + ' && (m_jj[0] > 500.)'

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
    'm_jjll': {'title': 'm_{jje#mu} [GeV]', 'bin': 10, 'xmin': 0, 'xmax': 4000},
    'dphi_jj_abs': {'title': '#Delta#phi_{jj}', 'bin': 30, 'xmin': 0, 'xmax': 3.1416},
    'deta_jj_abs': {'title': '#Delta#eta_{jj}', 'bin': 60, 'xmin': 0, 'xmax': 12.0},
    'el1_pt': {'title': 'Leading electron p_{T} [GeV]', 'bin': 40, 'xmin': 0, 'xmax': 200},
    'mu1_pt': {'title': 'Leading muon p_{T} [GeV]', 'bin': 40, 'xmin': 0, 'xmax': 200},
    'lep1_pt': {'title': 'Leading lepton p_{T} [GeV]', 'bin': 40, 'xmin': 0, 'xmax': 400},
    'lep2_pt': {'title': 'Subleading lepton p_{T} [GeV]', 'bin': 40, 'xmin': 0, 'xmax': 200},
    'm_ll': {'title': 'm_{e#mu} [GeV]', 'bin': 60, 'xmin': 0, 'xmax': 600},
    'dphi_em_abs': {'title': '#Delta#phi_{e#mu}', 'bin': 30, 'xmin': 0, 'xmax': 3.1416},
    'deta_em_abs': {'title': '#Delta#eta_{e#mu}', 'bin': 40, 'xmin': 0, 'xmax': 8.0},
    'zeta': {'title': 'Lepton centrality #zeta', 'bin': 50, 'xmin': -5.0, 'xmax': 5.0},
    'dphi_emMET': {'title': '#Delta#phi(e#mu,MET)', 'bin': 30, 'xmin': 0, 'xmax': 3.1416},
    'MET': {'title': 'Missing E_{T} [GeV]', 'bin': 40, 'xmin': 0, 'xmax': 1000},
}

for key, val in histoList.items():
    if 'name' not in val:
        val['name'] = key
