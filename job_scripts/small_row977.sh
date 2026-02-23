#!/bin/bash
#! SLURM job script for benchmark_small_row977
#! Based on ps.qsub template
#!
#SBATCH -J benchmark_small_row977
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
python -c "from run_parallel_config import run_parallel; run_parallel(r'[cH:2]1[cH:3][c:4]2[n:5]([n:6]1)[CH2:7][CH2:8][CH2:9][NH:10]2.[I:101][CH3:1]', r'[CH3:1][N:10]1[c:4]2[cH:3][cH:2][n:6][n:5]2[CH2:7][CH2:8][CH2:9]1', 'small_row977')"
