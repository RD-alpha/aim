#!/bin/bash
#! SLURM job script for benchmark_small_row926
#! Based on ps.qsub template
#!
#SBATCH -J benchmark_small_row926
#SBATCH -p CLUSTER
#SBATCH --nodes=1
#SBATCH --cpus-per-task=16
#SBATCH --time=12:50:00
#SBATCH --mail-type=ALL
#SBATCH --signal=B:USR1@60

source ~/.bashrc
export PATH=$HOME/.conda/envs/venv/bin:$PATH

SCRATCH=/scratch/$USER/$SLURM_JOB_ID
mkdir -p $SCRATCH
export SCRATCH

# Run the benchmark
python -c "from run_parallel_config import run_parallel; run_parallel(r'[O:101]=[CH:1][c:2]1[s:3][cH:4][c:5]([C:6]#[N:7])[cH:8]1.[NH2:9][OH:10].[H+:301]', r'[CH:1]([c:2]1[s:3][cH:4][c:5]([C:6]#[N:7])[cH:8]1)=[N:9][OH:10]', 'small_row926')"
