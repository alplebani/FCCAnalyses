#!/usr/bin/env python3

import argparse
import glob
import os
import subprocess


def get_args():
    '''
    Function to parse command line arguments.

    Returns:
        argparse.Namespace: Parsed command line arguments.
    '''

    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-f', '--folder', type=str, help='Name of the folder inside condor/ for the submission and log files.', required=True)
    parser.add_argument('-o', '--output', type=str, help='Output directory for the .edm4hep.root files.', default='/eos/home-a/alpleban/FCC/vbf_ww_lvlv/samples/mg_pp_vbf_ww_lvlv_5f_84TeV_TrackCov')
    parser.add_argument('-i', '--input', type=str, help='List of LHE fragments, one per line (default: condor/fragments.txt).', default=None)
    parser.add_argument('--delphes-card', type=str, help='Delphes card (default: gen/run_fragment.sh default).', default=None)
    parser.add_argument('--key4hep-setup', type=str, help='key4hep setup command + options (default: gen/run_fragment.sh default).', default=None)
    parser.add_argument('--flavour', type=str, help='lxplus JobFlavour.', default='workday')
    parser.add_argument('--events-per-job', type=int, help='Split each fragment into jobs of this many events (default: one job per fragment, events from the .cmd card).', default=None)
    parser.add_argument('--events-per-fragment', type=int, help='Events in each LHE fragment (only used with --events-per-job).', default=10000)
    parser.add_argument('--retry', help='Flag that determines whether you want to retry the jobs that did not print "Job FINISHED" (failed or killed)', action='store_true', default=False)
    args = parser.parse_args()
    return args


def get_finished_jobs(output_folder: str) -> list:
    '''
    Function that returns the jobs whose stdout contains "Job FINISHED". Jobs
    killed by Condor (e.g. wall time exceeded) leave no stdout, so they count
    as not finished.

    Args:
        output_folder (str): folder with the jobs' stdout files (<job>.txt)

    Returns:
        finished (list): names of the finished jobs (e.g. events_001453574_s2000)
    '''
    finished = []
    for out_file in glob.glob(os.path.join(output_folder, '*.txt')):
        with open(out_file, 'r') as f:
            if 'Job FINISHED' in f.read():
                finished.append(os.path.basename(out_file).replace('.txt', ''))
    return finished


def get_jobs(lhe_files: list, events_per_job: int, events_per_fragment: int) -> dict:
    '''
    Function that splits the LHE fragments into jobs.

    Args:
        lhe_files (list): paths of the LHE fragments
        events_per_job (int): events per job, or None for one job per fragment
        events_per_fragment (int): events in each LHE fragment

    Returns:
        jobs (dict): job name -> (LHE file, events, events to skip); events and
            events to skip are None for one job per fragment
    '''
    jobs = {}
    for lhe in lhe_files:
        fragment = os.path.basename(lhe).replace('.lhe.gz', '')
        if events_per_job is None:
            jobs[fragment] = (lhe, None, None)
            continue
        for skip in range(0, events_per_fragment, events_per_job):
            # same naming as gen/run_fragment.sh, so job names match output files
            jobs[f'{fragment}_s{skip}'] = (lhe, min(events_per_job, events_per_fragment - skip), skip)
    return jobs


def write_run_fragment(bash_file: str, run_fragment: str, output_dir: str, delphes_card: str, key4hep_setup: str, split: bool) -> None:
    '''
    Function that writes the job script: it sets this submission's options and calls
    gen/run_fragment.sh on the LHE fragment given as its first argument.

    Args:
        bash_file (str): path of the job script to write
        run_fragment (str): path of gen/run_fragment.sh
        output_dir (str): output directory for the .edm4hep.root files
        delphes_card (str): Delphes card, or None for the run_fragment.sh default
        key4hep_setup (str): key4hep setup command, or None for the run_fragment.sh default
        split (bool): whether the job also gets the number of events and events to skip

    Returns:
        None
    '''
    with open(bash_file, 'w') as of:
        of.write('#!/bin/bash\n')
        if delphes_card:
            of.write(f'export DELPHES_CARD={delphes_card}\n')
        if key4hep_setup:
            of.write(f'export KEY4HEP_SETUP="{key4hep_setup}"\n')
        if split:
            of.write(f'exec {run_fragment} "$1" {output_dir} "$2" "$3"\n')
        else:
            of.write(f'exec {run_fragment} "$1" {output_dir}\n')

    os.chmod(bash_file, 0o755)


def main(args, folder, log_folder, error_folder, output_folder, input_list, run_fragment):

    print(f'Running condor_submit.py with input file: {input_list}')
    print(f'Condor folder: {folder}')
    print(f'Output directory: {args.output}')

    user_input = input("Do you want to proceed with the submission? [y/n]: ")
    if user_input.lower() != 'y':
        print("Submission aborted.")
        return
    print("Proceeding with submission...")

    with open(input_list, 'r') as f:
        lhe_files = [line.strip() for line in f if line.strip()]
    split = args.events_per_job is not None
    jobs = get_jobs(lhe_files, args.events_per_job, args.events_per_fragment)

    if args.retry:
        print('Retrying failed or killed jobs')
        finished = get_finished_jobs(output_folder)
        jobs = {key: value for key, value in jobs.items() if key not in finished}
        if not jobs:
            print('No failed jobs found.')
            return

    bash_file = os.path.join(folder, 'run_fragment.sh')
    write_run_fragment(bash_file, run_fragment, args.output, args.delphes_card, args.key4hep_setup, split)

    sub_file = os.path.join(folder, 'submit.sub')
    with open(sub_file, 'w') as f:
        f.write("###################\n")
        f.write("### Job Options ###\n")
        f.write("###################\n")
        f.write(f"executable = {bash_file}\n")
        f.write('arguments = $(LHEFILE) $(NEVENTS) $(SKIP)\n' if split else 'arguments = $(LHEFILE)\n')
        # start at 2 GB and, if the job is held for exceeding memory, release it with 1.5x its measured usage
        f.write("request_memory = ifThenElse(MemoryUsage =!= undefined, MAX({MemoryUsage * 3/2, 2000}), 2000)\n")
        # hold jobs that have been running > 2h while using < 5% CPU
        f.write("periodic_hold = (JobStatus == 2) && (time() - EnteredCurrentStatus > 7200) && (RemoteUserCpu < 0.05 * (time() - EnteredCurrentStatus))\n")
        f.write('periodic_hold_reason = "Stuck: running > 2h with < 5% CPU"\n')
        f.write("periodic_hold_subcode = 42\n")
        # release (up to 3 starts) after: memory exceeded (34), stuck job (subcode 42), input transfer failure (13)
        f.write("periodic_release = ((HoldReasonCode == 34) || (HoldReasonCode == 3 && HoldReasonSubCode == 42) || (HoldReasonCode == 13)) && (NumJobStarts < 3)\n")
        f.write("request_CPUs = 1\n")
        f.write(f'+JobFlavour = "{args.flavour}"\n')
        f.write("max_retries = 2\n")
        name = f'vbf_ww_lvlv_{args.folder}'
        if args.retry:
            name = 'Retry_' + name
        f.write(f'+JobBatchName = "{name}"\n')
        f.write("\n")
        f.write("###################\n")
        f.write("### OutputFiles ###\n")
        f.write("###################\n")
        f.write(f"log    = {log_folder}/$(FRAGMENT).log\n")
        f.write(f"error  = {error_folder}/$(FRAGMENT).txt\n")
        f.write(f"output = {output_folder}/$(FRAGMENT).txt\n")
        f.write("getenv = False\n")
        f.write('MY.WantOS = "el9"\n')
        f.write("\n")
        f.write("#####################\n")
        f.write("### Queue jobs ###\n")
        f.write("#####################\n")
        if split:
            f.write("queue FRAGMENT, LHEFILE, NEVENTS, SKIP from (\n")
            for key, (lhe, n_events, skip) in jobs.items():
                f.write(f'    {key}, {lhe}, {n_events}, {skip}\n')
        else:
            f.write("queue FRAGMENT, LHEFILE from (\n")
            for key, (lhe, _, _) in jobs.items():
                f.write(f'    {key}, {lhe}\n')
        f.write(")\n")

    # submission files on /eos need the EosSubmit schedds (what "module load lxbatch/eossubmit" sets),
    # and the job's cwd is the submission folder
    eos_env = dict(os.environ, _myschedd_POOL='eossubmit', _condor_CONDOR_HOST='tweetybird04.cern.ch, tweetybird03.cern.ch')
    print(f'Submitting {len(jobs)} jobs with command: condor_submit {sub_file}')
    subprocess.run(['condor_submit', sub_file], cwd=folder, env=eos_env, check=True)
    subprocess.run(['condor_q'], env=eos_env)


if __name__ == "__main__":

    args = get_args()

    base_dir = os.path.dirname(os.path.abspath(__file__))
    condor_dir = os.path.join(base_dir, 'condor')
    run_fragment = os.path.join(base_dir, 'gen', 'run_fragment.sh')
    folder = os.path.join(condor_dir, args.folder)
    input_list = os.path.abspath(args.input) if args.input else os.path.join(condor_dir, 'fragments.txt')

    if not os.path.exists(folder):
        os.makedirs(folder)

    log_folder = os.path.join(folder, 'logs')
    if not os.path.exists(log_folder):
        os.makedirs(log_folder)
    error_folder = os.path.join(folder, 'errors')
    if not os.path.exists(error_folder):
        os.makedirs(error_folder)
    output_folder = os.path.join(folder, 'outputs')
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    if not os.path.exists(args.output):
        os.makedirs(args.output, exist_ok=True)

    main(args, folder, log_folder, error_folder, output_folder, input_list, run_fragment)
