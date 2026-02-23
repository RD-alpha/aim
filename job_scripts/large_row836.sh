#!/bin/bash
#! SLURM job script for benchmark_large_row836
#! Based on ps.qsub template
#!
#SBATCH -J benchmark_large_row836
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
python -c "from run_parallel_config import run_parallel; run_parallel(r'[CH3:19][O:20][c:21]1[cH:22][c:23]([CH:24]([CH3:25])[CH3:26])[c:27]2[c:28]([cH:29]1)[S:30](=[O:31])(=[O:32])[N:33]([CH2:34][O:35][C:36](=[O:37])[c:38]1[c:39]([Cl:40])[cH:41][cH:42][c:43]([OH:44])[c:45]1[Cl:46])[C:47]2=[O:48].[OH:101][CH2:1][CH2:2][CH:3]1[CH2:4][CH2:5][N:6]([C:7](=[O:8])[O:9][CH2:10][c:11]2[cH:12][cH:13][cH:14][cH:15][cH:16]2)[CH2:17][CH2:18]1.c1ccccc1[P:301](c2ccccc2)c3ccccc3.[O:302]=[C:303]([N:304]=[N:305]C(=O)OCC)OCC', r'[CH2:1]([CH2:2][CH:3]1[CH2:4][CH2:5][N:6]([C:7](=[O:8])[O:9][CH2:10][c:11]2[cH:12][cH:13][cH:14][cH:15][cH:16]2)[CH2:17][CH2:18]1)[O:44][c:43]1[cH:42][cH:41][c:39]([Cl:40])[c:38]([C:36]([O:35][CH2:34][N:33]2[S:30](=[O:31])(=[O:32])[c:28]3[c:27]([c:23]([CH:24]([CH3:25])[CH3:26])[cH:22][c:21]([O:20][CH3:19])[cH:29]3)[C:47]2=[O:48])=[O:37])[c:45]1[Cl:46]', 'large_row836')"
