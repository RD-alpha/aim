#!/bin/bash
#! SLURM job script for benchmark_small_row464
#! Based on ps.qsub template
#!
#SBATCH -J benchmark_small_row464
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
python -c "from run_parallel_config import run_parallel; run_parallel(r'[CH3:1][CH2:2][N:6]([CH2:5][CH3:4])[CH2:9][CH2:10][OH:11].[Br:101][CH2:7][CH3:8]', r'[CH3:1][CH2:2][N+:6]([CH2:5][CH3:4])([CH2:7][CH3:8])[CH2:9][CH2:10][OH:11]', 'small_row464')"
