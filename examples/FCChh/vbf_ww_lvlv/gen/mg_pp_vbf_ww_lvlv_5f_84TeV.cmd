! Pythia8 card: shower MadGraph LHE events for
! p p > j j l v l v (VBF WW -> lvlv, 5-flavor scheme) at sqrt(s) = 84 TeV.
! LO LHE sample (no POWHEG matching) - decays (W->lv) are already fixed
! at generator level, so no ResonanceDecayFilter is needed here.
!
! Used as-is by gen/run_delphes_pythia8.sh (single fragment) and as the
! template for condor/run_fragment.sh, which strips the Beams:* lines below
! and re-adds them pointing at each job's fragment.

! 1) Settings that will be used in a main program.
Main:numberOfEvents = 10000        ! number of events to generate (<= events in the LHE file)
Main:timesAllowErrors = 100        ! abort run after this many flawed events

! 2) Settings related to output in init(), next() and stat() functions.
Init:showChangedSettings = on      ! list changed settings
Init:showAllSettings = off         ! list all settings
Init:showChangedParticleData = on  ! list changed particle data
Init:showAllParticleData = off     ! list all particle data
Next:numberCount = 1000            ! print message every n events
Next:numberShowLHA = 1             ! print LHA information n times
Next:numberShowInfo = 1            ! print event information n times
Next:numberShowProcess = 1         ! print process record n times
Next:numberShowEvent = 1           ! print event record n times
Stat:showPartonLevel = off         ! additional statistics on MPI

! 3) Tell Pythia that LHEF input is used.
! Point this at one fragment of the sample (full list in condor/fragments.txt):
Beams:frameType = 4
Beams:setProductionScalesFromLHEF = off
Beams:LHEF = /eos/experiment/fcc/hh/generation/lhe/mg_pp_vbf_ww_lvlv_5f_84TeV/events_001453574.lhe.gz
