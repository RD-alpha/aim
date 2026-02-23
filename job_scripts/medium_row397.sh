#!/bin/bash
#! SLURM job script for benchmark_medium_row397
#! Based on ps.qsub template
#!
#SBATCH -J benchmark_medium_row397
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
python -c "from run_parallel_config import run_parallel; run_parallel(r'[OH:101][C:1]([c:2]1[cH:3][cH:4][cH:5][c:6]([O:7][CH3:8])[cH:9]1)=[O:10].[N:11]#[C:12][c:13]1[cH:14][cH:15][c:16]([CH2:17][NH2:18])[c:19]([OH:20])[cH:21]1.[N:301](=[C:302]=[N:303]C1CCCCC1)C2CCCCC2', r'[C:1]([c:2]1[cH:3][cH:4][cH:5][c:6]([O:7][CH3:8])[cH:9]1)(=[O:10])[NH:18][CH2:17][c:16]1[cH:15][cH:14][c:13]([C:12]#[N:11])[cH:21][c:19]1[OH:20]', 'medium_row397')"
