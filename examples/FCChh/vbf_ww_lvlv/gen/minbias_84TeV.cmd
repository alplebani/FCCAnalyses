! Pythia8 card: minimum-bias p p collisions at sqrt(s) = 84 TeV, used to
! build the Delphes pile-up file (MinBias.pileup) for FCChh_II_PileUp.tcl.
! Adapted from Delphes' examples/Pythia8/generatePileUp.cmnd.
!
! Used as the template for gen/run_minbias.sh, which strips the
! Main:numberOfEvents and Random:* lines below and re-adds them per job.

! 1) Settings that will be used in a main program.
Main:numberOfEvents = 1000         ! number of events to generate
Main:timesAllowErrors = 100        ! abort run after this many flawed events

! 2) Settings related to output in init(), next() and stat() functions.
Init:showChangedSettings = on      ! list changed settings
Init:showAllSettings = off         ! list all settings
Init:showChangedParticleData = on  ! list changed particle data
Init:showAllParticleData = off     ! list all particle data
Next:numberCount = 1000            ! print message every n events
Next:numberShowInfo = 1            ! print event information n times
Next:numberShowProcess = 1         ! print process record n times
Next:numberShowEvent = 1           ! print event record n times
Stat:showPartonLevel = off         ! additional statistics on MPI
Random:setSeed = on
Random:seed = 10                   ! must differ between jobs

! 3) Beam parameter settings.
Beams:idA = 2212                   ! first beam, p = 2212
Beams:idB = 2212                   ! second beam, p = 2212
Beams:eCM = 84000.                 ! CM energy of collision

! 4) Processes: total inelastic + elastic cross section (ND, SD, DD, CD, elastic).
! Default tune (Monash), same as the signal card mg_pp_vbf_ww_lvlv_5f_84TeV.cmd.
SoftQCD:all = on
