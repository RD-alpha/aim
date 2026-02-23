#!/bin/bash
#! SLURM job script for benchmark_medium_row263
#! Based on ps.qsub template
#!
#SBATCH -J benchmark_medium_row263
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
python -c "from run_parallel_config import run_parallel; run_parallel(r'[N:9]#[C:10][c:11]1[cH:12][cH:13][c:14]([NH:15][C:16](=[O:17])[C:18](=[O:19])[CH:20]2[CH2:21][CH2:22][CH2:23][CH2:24][CH2:25]2)[cH:26][c:27]1[Cl:28].[CH:1]#[C:2][c:3]1[cH:4][cH:5][cH:6][cH:7][cH:8]1.[NH2-:301].[Na+]', r'[C:1](#[C:2][c:3]1[cH:4][cH:5][cH:6][cH:7][cH:8]1)[C:18]([C:16]([NH:15][c:14]1[cH:13][cH:12][c:11]([C:10]#[N:9])[c:27]([Cl:28])[cH:26]1)=[O:17])([OH:19])[CH:20]1[CH2:21][CH2:22][CH2:23][CH2:24][CH2:25]1', 'medium_row263')"
