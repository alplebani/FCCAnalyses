'''
Analysis for FCC-hh VBF WW -> lvlv (mg_pp_vbf_ww_lvlv_5f_84TeV).
Adapted from examples/FCChh/vbf_hww/analysis_stage1.py (VBF H->WW).

NOTE: three helper functions used by the vbf_hww template
(AnalysisFCChh::get_lepton_centrality, get_mT_hww, get_ntrk) are not actually
defined in this FCCAnalyses build's analyzers/dataframe/Analysis_FCChh.{h,cc}
(checked both the source tree and the installed headers) - so the
corresponding variables (MT, lep_cent, n_RecoTracks) are left out here rather
than copied in broken. Everything else (electrons/muons/jets/MET/b-tagging/
pair-mass/angular-distance helpers) is confirmed present and used as-is.
'''
import vbf_ww_lvlv.analysis_config as analysis_config


# Mandatory: Analysis class where the user defines the operations on the
# dataframe.
class Analysis():
    '''
    VBF WW -> lvlv (e/mu + neutrinos) analysis.
    '''
    def __init__(self, cmdline_args):
        self.process_list = analysis_config.process_list
        self.input_dir = analysis_config.input_dir
        self.output_dir = analysis_config.stage1_output

        # Optional: analysisName, default is ''
        self.analysis_name = 'FCC-hh VBF WW->lvlv analysis'

        # Optional: number of threads to run on, default is 1
        # self.n_threads = 4

        # Optional: running on HTCondor, default is False
        self.run_batch = False

        # Optional: Use weighted events (EventHeader.weight) - for this LO,
        # unweighted MadGraph+Pythia8 sample, weight is always 1.0, but the
        # field is read regardless so this stays forward-compatible with any
        # NLO/weighted sample added later.
        self.do_weighted = True

        # Optional: read the input files with podio::DataSource
        self.use_data_source = False

        # Optional: test file used with `fccanalysis run ... --test`
        self.test_file = "/eos/user/a/alpleban/FCC/vbf_ww_lvlv/samples/mg_pp_vbf_ww_lvlv_5f_84TeV/events_015959360.edm4hep.root"

    # Mandatory: analyzers function to define the analysis graph, please make
    # sure you return the dataframe, in this example it is dframe2
    def analyzers(self, dframe):
        '''
        Analysis graph.
        '''
        dframe2 = (
            dframe

            ########################################### DEFINITION OF VARIABLES ###########################################

            # generator event weight
            .Define("weight", "EventHeader.weight")

            ########################################### Truth-level W+W- check ###########################################
            .Define("hardMC", "FCCAnalyses::MCParticle::sel_genStatus(22)(Particle)")
            .Define("n_hardMC", "FCCAnalyses::MCParticle::get_n(hardMC)")

            .Define("genWp", "FCCAnalyses::MCParticle::sel_pdgID(24, false)(hardMC)")
            .Define("genWm", "FCCAnalyses::MCParticle::sel_pdgID(-24, false)(hardMC)")
            .Define("n_genWp", "FCCAnalyses::MCParticle::get_n(genWp)")
            .Define("n_genWm", "FCCAnalyses::MCParticle::get_n(genWm)")

            ########################################### Electrons ###########################################
            .Define("electrons", "FCCAnalyses::ReconstructedParticle::get(Electron_objIdx.index, ReconstructedParticles)")
            .Define("selpt_el", "FCCAnalyses::ReconstructedParticle::sel_pt(10.)(electrons)")
            .Define("sel_el_unsort", "FCCAnalyses::ReconstructedParticle::sel_eta(4)(selpt_el)")
            .Define("sel_el", "AnalysisFCChh::SortParticleCollection(sel_el_unsort)")  # sort by pT

            .Define("n_el", "FCCAnalyses::ReconstructedParticle::get_n(sel_el)")
            .Define("el1_e", "FCCAnalyses::ReconstructedParticle::get_e(sel_el)[0]")
            .Define("el1_pt", "FCCAnalyses::ReconstructedParticle::get_pt(sel_el)[0]")
            .Define("el1_eta", "FCCAnalyses::ReconstructedParticle::get_eta(sel_el)[0]")
            .Define("el1_phi", "FCCAnalyses::ReconstructedParticle::get_phi(sel_el)[0]")

            ########################################### Muons ###########################################
            .Define("muons", "FCCAnalyses::ReconstructedParticle::get(Muon_objIdx.index, ReconstructedParticles)")
            .Define("selpt_mu", "FCCAnalyses::ReconstructedParticle::sel_pt(10.)(muons)")
            .Define("sel_mu_unsort", "FCCAnalyses::ReconstructedParticle::sel_eta(4)(selpt_mu)")
            .Define("sel_mu", "AnalysisFCChh::SortParticleCollection(sel_mu_unsort)")  # sort by pT

            .Define("n_mu", "FCCAnalyses::ReconstructedParticle::get_n(sel_mu)")
            .Define("mu1_e", "FCCAnalyses::ReconstructedParticle::get_e(sel_mu)[0]")
            .Define("mu1_pt", "FCCAnalyses::ReconstructedParticle::get_pt(sel_mu)[0]")
            .Define("mu1_eta", "FCCAnalyses::ReconstructedParticle::get_eta(sel_mu)[0]")
            .Define("mu1_phi", "FCCAnalyses::ReconstructedParticle::get_phi(sel_mu)[0]")

            # opposite-flavor e-mu pair (the signature final state: W->ev + W->muv)
            .Define("em_pairs_unmerged", "AnalysisFCChh::getDFOSPairs(sel_el,sel_mu)")
            .Define("em_pairs", "AnalysisFCChh::merge_pairs(em_pairs_unmerged)")
            .Define("m_em", "FCCAnalyses::ReconstructedParticle::get_mass(em_pairs)")

            ########################################### MET (from the two neutrinos) ###########################################
            .Define("MET", "FCCAnalyses::ReconstructedParticle::get_pt(MissingET)")
            .Define("MET_x", "FCCAnalyses::ReconstructedParticle::get_px(MissingET)")
            .Define("MET_y", "FCCAnalyses::ReconstructedParticle::get_py(MissingET)")
            .Define("MET_phi", "FCCAnalyses::ReconstructedParticle::get_phi(MissingET)")

            ########################################### Jets (VBF tag jets) ###########################################
            .Define("selected_jets", "ReconstructedParticle::sel_pt(30.)(Jet)")
            .Define("sel_jets", "AnalysisFCChh::SortParticleCollection(selected_jets)")
            .Define("n_jets", "FCCAnalyses::ReconstructedParticle::get_n(sel_jets)")
            .Define("j1_pt", "FCCAnalyses::ReconstructedParticle::get_pt(sel_jets)[0]")
            .Define("j1_eta", "FCCAnalyses::ReconstructedParticle::get_eta(sel_jets)[0]")
            .Define("j1_phi", "FCCAnalyses::ReconstructedParticle::get_phi(sel_jets)[0]")
            .Define("j2_pt", "FCCAnalyses::ReconstructedParticle::get_pt(sel_jets)[1]")
            .Define("j2_eta", "FCCAnalyses::ReconstructedParticle::get_eta(sel_jets)[1]")
            .Define("j2_phi", "FCCAnalyses::ReconstructedParticle::get_phi(sel_jets)[1]")

            .Define("centraljets", "FCCAnalyses::ReconstructedParticle::sel_eta(2.5)(selected_jets)")
            .Define("n_centraljets", "FCCAnalyses::ReconstructedParticle::get_n(centraljets)")

            .Define("jj_pairs_unmerged", "AnalysisFCChh::getPairs(sel_jets)")  # leading-pT pair of all possible
            .Define("jj_pairs", "AnalysisFCChh::merge_pairs(jj_pairs_unmerged)")
            .Define("m_jj", "FCCAnalyses::ReconstructedParticle::get_mass(jj_pairs)")
            .Define("pt_jj", "FCCAnalyses::ReconstructedParticle::get_pt(jj_pairs)")

            # VBF WW identification variables
            .Define("dphi_em", 'AnalysisFCChh::get_angularDist_pair(em_pairs_unmerged,"dPhiAbs")')
            .Define("deta_em", 'AnalysisFCChh::get_angularDist_pair(em_pairs_unmerged,"dEta")')
            .Define("dphi_jj", 'AnalysisFCChh::get_angularDist_pair(jj_pairs_unmerged,"dPhiAbs")')
            .Define("deta_jj", 'AnalysisFCChh::get_angularDist_pair(jj_pairs_unmerged,"dEta")')
            .Define("dphi_emMET", 'AnalysisFCChh::get_angularDist_MET(em_pairs,MissingET,"dPhiAbs")')

            # b-tagged jets, medium and loose working points (bit 1/0, see
            # https://github.com/delphes/delphes/blob/master/cards/FCC/scenarios/FCChh_I.tcl)
            .Define("b_tagged_jets_medium", "AnalysisFCChh::get_tagged_jets(Jet, Jet_HF_tags, _Jet_HF_tags_particle, _Jet_HF_tags_parameters, 1)")
            .Define("selpt_bjets", "FCCAnalyses::ReconstructedParticle::sel_pt(30.)(b_tagged_jets_medium)")
            .Define("sel_bjets_unsort", "FCCAnalyses::ReconstructedParticle::sel_eta(4)(selpt_bjets)")
            .Define("sel_bjets", "AnalysisFCChh::SortParticleCollection(sel_bjets_unsort)")
            .Define("n_bjets", "FCCAnalyses::ReconstructedParticle::get_n(sel_bjets)")

            .Define("b_tagged_jets_loose", "AnalysisFCChh::get_tagged_jets(Jet, Jet_HF_tags, _Jet_HF_tags_particle, _Jet_HF_tags_parameters, 0)")
            .Define("selpt_bjets_loose", "FCCAnalyses::ReconstructedParticle::sel_pt(20.)(b_tagged_jets_loose)")
            .Define("sel_bjets_loose_unsort", "FCCAnalyses::ReconstructedParticle::sel_eta(4)(selpt_bjets_loose)")
            .Define("sel_bjets_loose", "AnalysisFCChh::SortParticleCollection(sel_bjets_loose_unsort)")
            .Define("n_bjets_loose", "FCCAnalyses::ReconstructedParticle::get_n(sel_bjets_loose)")

            ########################################### APPLY PRE-SELECTION ###########################################
            # truth-level sanity check: this is a VBF WW sample, every event
            # should have one W+ and one W- at the hard-process level
            .Filter("n_hardMC>0")
            .Filter("n_genWp>=1 && n_genWm>=1")
            # exactly one electron and one muon (the direct e+mu-/e-mu+
            # channels this LHE sample was generated with - some tau->e/mu
            # leptonic decays from the shower pass this too)
            .Filter("n_el == 1")
            .Filter("n_mu == 1")
            # at least the two VBF tag jets
            .Filter("n_jets > 1")
        )
        return dframe2

    # Mandatory: output function, please make sure you return the branch list
    # as a python list
    def output(self):
        '''
        Output variables which will be saved to output root file.
        '''
        branch_list = [
            'weight',
            'n_el', 'el1_pt', 'el1_eta', 'el1_phi',
            'n_mu', 'mu1_pt', 'mu1_eta', 'mu1_phi',
            'm_em', 'dphi_em', 'deta_em',
            'MET', 'MET_x', 'MET_y', 'MET_phi',
            'n_jets', 'n_bjets', 'n_bjets_loose', 'n_centraljets',
            'j1_pt', 'j1_eta', 'j1_phi', 'j2_pt', 'j2_eta', 'j2_phi',
            'm_jj', 'dphi_jj', 'deta_jj', 'pt_jj',
            'dphi_emMET',
            'n_genWp', 'n_genWm',
        ]
        return branch_list
