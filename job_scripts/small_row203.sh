#!/bin/bash
#! SLURM job script for benchmark_small_row203
#! Based on ps.qsub template
#!
#SBATCH -J benchmark_small_row203
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
python -c "from run_parallel_config import run_parallel; run_parallel(r'[Cl:101][CH2:1][C:2](=[O:3])[NH:4][CH2:5][C@H:6]([OH:7])[CH2:8][OH:9].[H-:301].[Na+]', r'[CH2:1]1[C:2](=[O:3])[NH:4][CH2:5][C@@H:6]([CH2:8][OH:9])[O:7]1', 'small_row203')"
