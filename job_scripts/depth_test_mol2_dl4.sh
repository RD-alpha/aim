#!/bin/bash
#! SLURM job script for depth_test_depth_test_mol2_dl4
#!
#SBATCH -J depth_test_mol2_dl4
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
echo "BENCHMARK_LABEL: depth_test_mol2_dl4"
echo "DEPTH_LIMIT: 4"
echo "=========================================="

# Run depth test with depth_limit as argument to run_parallel
python -c "from run_parallel_config import run_parallel; run_parallel(r'[CH3:1][CH2:2][N:6]([CH2:5][CH3:4])[CH2:9][CH2:10][OH:11].[Br:101][CH2:7][CH3:8]', r'C', 'depth_test_mol2_dl4', depth_limit=4)"
