#!/usr/bin/env python3

import argparse
import glob
import os
import subprocess
import sys


def get_args():
    '''
    Function to parse command line arguments.

    Returns:
        argparse.Namespace: Parsed command line arguments.
    '''

    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-f', '--folder', type=str, help='Name of the folder inside condor/ for the submission and log files.', required=True)
    parser.add_argument('-p', '--process', type=str, help='Process (sample folder under analysis_config.input_dir) to run stage 1 on.', default='mg_pp_vbf_ww_lvlv_5f_84TeV_TrackCov')
    parser.add_argument('--key4hep-setup', type=str, help='key4hep setup command + options (must match the FCCAnalyses build).', default='/cvmfs/sw.hsf.org/key4hep/setup.sh -r 2024-10-03')
    parser.add_argument('--flavour', type=str, help='lxplus JobFlavour.', default='espresso')
    parser.add_argument('--retry', help='Flag that determines whether you want to retry the jobs without "Job FINISHED"', action='store_true', default=False)
    args = parser.parse_args()
    return args


def get_unfinished_jobs(output_folder) -> list:
    '''
    Function that returns the jobs whose stdout doesn't contain "Job FINISHED"

    Returns:
        unfinished (list): names of the unfinished jobs (e.g. events_001453574)
    '''
    unfinished = []
    for out_file in glob.glob(os.path.join(output_folder, '*.txt')):
        with open(out_file, 'r') as f:
            if 'Job FINISHED' not in f.read():
                unfinished.append(os.path.basename(out_file).replace('.txt', ''))
    return unfinished


def write_job_script(bash_file, fcc_dir, stage1_script, key4hep_setup):
    '''
    Function that writes the job script: it runs fccanalysis stage 1 on the input file given
    as its first argument, writing locally and copying to the output file given as the second.
    '''
    with open(bash_file, 'w') as of:
        of.write('#!/bin/bash\n')
        of.write('set -eo pipefail\n')
        of.write("trap 'echo \"Job FAILED\"' ERR\n")
        of.write(f'source {key4hep_setup}\n')
        of.write(f'source {fcc_dir}/setup.sh\n')
        of.write(f'export PYTHONPATH={fcc_dir}/examples/FCChh:$PYTHONPATH\n')
        # write in the job's scratch dir and copy at the end, so a killed job leaves no partial output
        of.write(f'fccanalysis run {stage1_script} --files-list "$1" --output "$PWD/$(basename "$2")"\n')
        of.write('cp "$PWD/$(basename "$2")" "$2"\n')
        of.write('echo "Job FINISHED"\n')

    os.chmod(bash_file, 0o755)


def main(args, folder, log_folder, error_folder, output_folder, input_files, stage1_dir, job_script_args):

    print(f'Running stage 1 on {len(input_files)} files of process {args.process}')
    print(f'Condor folder: {folder}')
    print(f'Output directory: {stage1_dir}')

    user_input = input("Do you want to proceed with the submission? [y/n]: ")
    if user_input.lower() != 'y':
        print("Submission aborted.")
        return
    print("Proceeding with submission...")

    jobs = {os.path.basename(path).replace('.edm4hep.root', ''): path for path in input_files}

    if args.retry:
        print('Retrying unfinished jobs')
        unfinished = get_unfinished_jobs(output_folder)
        jobs = {key: value for key, value in jobs.items() if key in unfinished}
        if not jobs:
            print('No unfinished jobs found.')
            return

    os.makedirs(stage1_dir, exist_ok=True)

    bash_file = os.path.join(folder, 'run_stage1.sh')
    write_job_script(bash_file, *job_script_args)

    sub_file = os.path.join(folder, 'submit.sub')
    with open(sub_file, 'w') as f:
        f.write("###################\n")
        f.write("### Job Options ###\n")
        f.write("###################\n")
        f.write(f"executable = {bash_file}\n")
        # do_plots.py/run_final_analysis.py pick up <process>/chunk*.root
        f.write(f'arguments = $(INFILE) {stage1_dir}/chunk_$(JOB).root\n')
        f.write("request_memory = ifThenElse(MemoryUsage =!= undefined, MAX({MemoryUsage * 3/2, 2000}), 2000)\n")
        f.write("periodic_release = (HoldReasonCode == 34) && (NumJobStarts < 3)\n")
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
        f.write(f"log    = {log_folder}/$(JOB).log\n")
        f.write(f"error  = {error_folder}/$(JOB).txt\n")
        f.write(f"output = {output_folder}/$(JOB).txt\n")
        f.write("getenv = False\n")
        f.write('MY.WantOS = "el9"\n')
        f.write("\n")
        f.write("#####################\n")
        f.write("### Queue jobs ###\n")
        f.write("#####################\n")
        f.write("queue JOB, INFILE from (\n")
        for key, value in jobs.items():
            f.write(f'    {key}, {value}\n')
        f.write(")\n")

    # submission files on /eos need the EosSubmit schedds (what "module load lxbatch/eossubmit" sets)
    eos_env = dict(os.environ, _myschedd_POOL='eossubmit', _condor_CONDOR_HOST='tweetybird04.cern.ch, tweetybird03.cern.ch')
    print(f'Submitting {len(jobs)} jobs with command: condor_submit {sub_file}')
    subprocess.run(['condor_submit', sub_file], cwd=folder, env=eos_env, check=True)
    subprocess.run(['condor_q'], env=eos_env)


if __name__ == "__main__":

    args = get_args()

    base_dir = os.path.dirname(os.path.abspath(__file__))
    fcc_dir = os.path.abspath(os.path.join(base_dir, '..', '..', '..'))
    stage1_script = os.path.join(base_dir, 'analysis_stage1.py')
    folder = os.path.join(base_dir, 'condor', args.folder)

    # analysis_config only holds plain values, safe to import here
    sys.path.insert(0, os.path.dirname(base_dir))
    from vbf_ww_lvlv import analysis_config

    input_files = sorted(glob.glob(os.path.join(analysis_config.input_dir, args.process, '*.root')))
    stage1_dir = os.path.join(analysis_config.stage1_output, args.process)

    log_folder = os.path.join(folder, 'logs')
    error_folder = os.path.join(folder, 'errors')
    output_folder = os.path.join(folder, 'outputs')
    for d in (log_folder, error_folder, output_folder):
        os.makedirs(d, exist_ok=True)

    main(args, folder, log_folder, error_folder, output_folder, input_files, stage1_dir,
         (fcc_dir, stage1_script, args.key4hep_setup))
