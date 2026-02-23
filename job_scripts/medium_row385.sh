#!/bin/bash
#! SLURM job script for benchmark_medium_row385
#! Based on ps.qsub template
#!
#SBATCH -J benchmark_medium_row385
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
python -c "from run_parallel_config import run_parallel; run_parallel(r'[CH3:7][c:8]1[cH:9][cH:10][cH:11][c:12]([NH:13][c:14]2[cH:15][c:16]([NH:17][c:18]3[cH:19][cH:20][cH:21][c:22]([OH:23])[cH:24]3)[n:25][cH:26][n:27]2)[cH:28]1.[Cl:101][CH2:1][CH2:2][CH2:3][N:4]([CH3:5])[CH3:6].[H-:301].[Na+]', r'[CH2:1]([CH2:2][CH2:3][N:4]([CH3:5])[CH3:6])[O:23][c:22]1[cH:21][cH:20][cH:19][c:18]([NH:17][c:16]2[cH:15][c:14]([NH:13][c:12]3[cH:11][cH:10][cH:9][c:8]([CH3:7])[cH:28]3)[n:27][cH:26][n:25]2)[cH:24]1', 'medium_row385')"
