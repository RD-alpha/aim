#!/bin/bash
#! SLURM job script for benchmark_medium_row968
#! Based on ps.qsub template
#!
#SBATCH -J benchmark_medium_row968
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
python -c "from run_parallel_config import run_parallel; run_parallel(r'[CH3:13][C:14]([CH3:15])([CH3:16])[O:17][C:18](=[O:19])[N:20]1[CH2:21][CH2:22][CH:23]([NH2:24])[CH2:25][CH2:26]1.[O:101]=[CH:1][c:2]1[c:3]([NH:4][C:5]([O:6][CH2:7][CH3:8])=[O:9])[cH:10][s:11][cH:12]1.[H+:301].[BH3-:302]C#N.[Na+]', r'[CH2:1]([c:2]1[c:3]([NH:4][C:5]([O:6][CH2:7][CH3:8])=[O:9])[cH:10][s:11][cH:12]1)[NH:24][CH:23]1[CH2:22][CH2:21][N:20]([C:18]([O:17][C:14]([CH3:13])([CH3:15])[CH3:16])=[O:19])[CH2:26][CH2:25]1', 'medium_row968')"
