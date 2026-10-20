'''
Plotting stage for FCC-hh VBF WW -> lvlv.
Adapted from examples/FCChh/vbf_hww/analysis_plots.py. Only one process/
sample exists so far (no backgrounds produced yet), so this is a simple
single-process plot rather than a signal/background stack - extend the
`procs`/`colors`/`legend` dicts below once more samples (ttbar, Z+jets, ...)
are produced through the same Delphes/Condor pipeline and added to
analysis_config.process_list.
'''
import ROOT
from analysis_final import histoList
import vbf_ww_lvlv.analysis_config as analysis_config

# global parameters
intLumi = 30e+06  # in pb-1
ana_tex = 'VBF W^{+}W^{-} #rightarrow e#mu + #nu#nu'
delphesVersion = '3.5.1'
energy = 84
collider = 'FCC-hh'
inputDir = analysis_config.final_output
formats = ['pdf']
yaxis = ['log']
stacksig = ['nostack']
outdir = analysis_config.plots_output
plotStatUnc = True

variables = histoList.keys()

# Selections to plot, named the same as in analysis_final.py's cutList
extralabel = {}
extralabel['sel0_all'] = 'Preselection events'
extralabel['sel1_bjeteveto'] = 'b-jet veto'
extralabel['sel2_jeteveto'] = '2-jet exclusive'
extralabel['sel3_both'] = '2-jet exclusive and b-jet veto'
extralabel['sel4_mjj'] = 'm_{jj}, #Delta#eta_{jj} cut applied'
extralabel['sel5_mem'] = 'm_{e#mu} cut applied'

selections = {}
selections['vbf_ww_lvlv'] = extralabel.keys()

colors = {}
colors['vbf_ww_lvlv'] = ROOT.kRed

# this is selection : signal/backgrounds category : {final histo label : [set of input procs]}
plots = {}
plots['vbf_ww_lvlv'] = {}
plots['vbf_ww_lvlv']['signal'] = {}
plots['vbf_ww_lvlv']['signal']['vbf_ww_lvlv'] = ['mg_pp_vbf_ww_lvlv_5f_84TeV']
plots['vbf_ww_lvlv']['backgrounds'] = {}

legend = {}
legend['vbf_ww_lvlv'] = 'VBF W^{+}W^{-}#rightarrow e#mu#nu#nu'
