#!/bin/bash
#! SLURM job script for benchmark_small_row773
#! Based on ps.qsub template
#!
#SBATCH -J benchmark_small_row773
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
python -c "from run_parallel_config import run_parallel; run_parallel(r'[N:2]#[C:3][c:4]1[cH:5][cH:6][cH:7][n:8][n:9]1.[Li+:301].[AlH4-:302].[OH2:303].[OH2:304]', r'[NH2:2][CH2:3][c:4]1[cH:5][cH:6][cH:7][n:8][n:9]1', 'small_row773')"
