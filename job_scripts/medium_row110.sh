#!/bin/bash
#! SLURM job script for benchmark_medium_row110
#! Based on ps.qsub template
#!
#SBATCH -J benchmark_medium_row110
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
python -c "from run_parallel_config import run_parallel; run_parallel(r'[O:11]=[C:12]1[C:13]2=[C:14]([S:15][CH2:16][CH2:17][S:18]2)[CH:19]([OH:20])[N:21]1[c:22]1[cH:23][cH:24][c:25]([Cl:26])[cH:27][n:28]1.[Cl:101][C:1]([N:2]1[CH2:3][CH2:4][N:5]([CH2:6][CH3:7])[CH2:8][CH2:9]1)=[O:10].[H-:301].[Na+]', r'[C:1]([N:2]1[CH2:3][CH2:4][N:5]([CH2:6][CH3:7])[CH2:8][CH2:9]1)(=[O:10])[O:20][CH:19]1[C:14]2=[C:13]([C:12](=[O:11])[N:21]1[c:22]1[cH:23][cH:24][c:25]([Cl:26])[cH:27][n:28]1)[S:18][CH2:17][CH2:16][S:15]2', 'medium_row110')"
