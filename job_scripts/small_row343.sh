#!/bin/bash
#! SLURM job script for benchmark_small_row343
#! Based on ps.qsub template
#!
#SBATCH -J benchmark_small_row343
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
python -c "from run_parallel_config import run_parallel; run_parallel(r'[O:1]=[CH:2][c:3]1[cH:4][n:5][cH:6][cH:7][c:8]1[Br:9].[BH4-:301].[CH3][OH1:302]', r'[OH:1][CH2:2][c:3]1[cH:4][n:5][cH:6][cH:7][c:8]1[Br:9]', 'small_row343')"
