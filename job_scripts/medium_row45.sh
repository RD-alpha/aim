#!/bin/bash
#! SLURM job script for benchmark_medium_row45
#! Based on ps.qsub template
#!
#SBATCH -J benchmark_medium_row45
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
python -c "from run_parallel_config import run_parallel; run_parallel(r'[CH3:1][C:2]([CH3:3])([CH3:4])[O:5][C:6](=[O:7])[N:8]1[CH2:9][CH2:10][CH:11]([N:12]2[C:13](=[O:14])[NH:15][CH2:16][C@H:17]2[c:18]2[cH:19][cH:20][cH:21][cH:22][cH:23]2)[CH2:24][CH2:25]1.[CH3:26][N:27]=[C:28]=[O:29]', r'[CH3:1][C:2]([CH3:3])([CH3:4])[O:5][C:6](=[O:7])[N:8]1[CH2:9][CH2:10][CH:11]([N:12]2[C:13](=[O:14])[N:15]([C:28]([NH:27][CH3:26])=[O:29])[CH2:16][C@H:17]2[c:18]2[cH:19][cH:20][cH:21][cH:22][cH:23]2)[CH2:24][CH2:25]1', 'medium_row45')"
