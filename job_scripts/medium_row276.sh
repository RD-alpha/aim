#!/bin/bash
#! SLURM job script for benchmark_medium_row276
#! Based on ps.qsub template
#!
#SBATCH -J benchmark_medium_row276
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
python -c "from run_parallel_config import run_parallel; run_parallel(r'[CH3:8][O:9][C:10](=[O:11])[c:12]1[cH:13][c:14]([OH:15])[cH:16][c:17]([O:18][c:19]2[cH:20][cH:21][c:22]([N+:23](=[O:24])[OH:25])[cH:26][cH:27]2)[cH:28]1.[Br:101][CH2:1][c:2]1[cH:3][cH:4][cH:5][cH:6][cH:7]1.[H-:301].[Na+]', r'[CH2:1]([c:2]1[cH:3][cH:4][cH:5][cH:6][cH:7]1)[O:15][c:14]1[cH:13][c:12]([C:10]([O:9][CH3:8])=[O:11])[cH:28][c:17]([O:18][c:19]2[cH:20][cH:21][c:22]([N+:23](=[O:24])[OH:25])[cH:26][cH:27]2)[cH:16]1', 'medium_row276')"
