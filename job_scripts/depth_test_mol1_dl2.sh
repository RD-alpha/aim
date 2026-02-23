#!/bin/bash
#! SLURM job script for depth_test_depth_test_mol1_dl2
#!
#SBATCH -J depth_test_mol1_dl2
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

# Print benchmark label for identification
echo "BENCHMARK_LABEL: depth_test_mol1_dl2"
echo "DEPTH_LIMIT: 2"
echo "=========================================="

# Run depth test with depth_limit as argument to run_parallel
python -c "from run_parallel_config import run_parallel; run_parallel(r'[Cl:101][CH2:1][C:2](=[O:3])[NH:4][CH2:5][C@H:6]([OH:7])[CH2:8][OH:9].[H-:301].[Na+]', r'C', 'depth_test_mol1_dl2', depth_limit=2)"
