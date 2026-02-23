#!/bin/bash
#! SLURM job script for benchmark_small_row187
#! Based on ps.qsub template
#!
#SBATCH -J benchmark_small_row187
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
python -c "from run_parallel_config import run_parallel; run_parallel(r'[SH:4][c:5]1[cH:6][cH:7][cH:8][s:9]1.[Br:101][CH2:1][CH2:2][Br:3].[H-:301].[Na+]', r'[CH2:1]([CH2:2][Br:3])[S:4][c:5]1[cH:6][cH:7][cH:8][s:9]1', 'small_row187')"
