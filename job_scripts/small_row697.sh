#!/bin/bash
#! SLURM job script for benchmark_small_row697
#! Based on ps.qsub template
#!
#SBATCH -J benchmark_small_row697
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
python -c "from run_parallel_config import run_parallel; run_parallel(r'[CH3:1][C:2]1([CH3:3])[C:4](=[O:5])[CH:6]=[CH:7][C:8]1=[O:9].[BH4-:301].[CH3][OH1:302]', r'[CH3:1][C:2]1([CH3:3])[CH:4]([OH:5])[CH:6]=[CH:7][C:8]1=[O:9]', 'small_row697')"
