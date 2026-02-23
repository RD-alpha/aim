#!/bin/bash
#! SLURM job script for depth_test_depth_test_mol0_dl1
#!
#SBATCH -J depth_test_mol0_dl1
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
echo "BENCHMARK_LABEL: depth_test_mol0_dl1"
echo "DEPTH_LIMIT: 1"
echo "=========================================="

# Run depth test with depth_limit as argument to run_parallel
python -c "from run_parallel_config import run_parallel; run_parallel(r'[SH:4][c:5]1[cH:6][cH:7][cH:8][s:9]1.[Br:101][CH2:1][CH2:2][Br:3].[H-:301].[Na+]', r'C', 'depth_test_mol0_dl1', depth_limit=1)"
