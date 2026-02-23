#!/bin/bash
#! SLURM job script for benchmark_large_row720
#! Based on ps.qsub template
#!
#SBATCH -J benchmark_large_row720
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
python -c "from run_parallel_config import run_parallel; run_parallel(r'[CH3:10][O:11][CH2:12][CH2:13][CH2:14][c:15]1[cH:16][c:17]([OH:18])[cH:19][c:20]([CH2:21][N:22]([C:23](=[O:24])[C@H:25]2[CH2:26][N:27]([C:28](=[O:29])[O:30][C:31]([CH3:32])([CH3:33])[CH3:34])[CH2:35][CH2:36][C@@H:37]2[c:38]2[cH:39][cH:40][c:41]([O:42][CH2:43][CH2:44][O:45][c:46]3[c:47]([Cl:48])[cH:49][c:50]([CH3:51])[cH:52][c:53]3[Cl:54])[cH:55][cH:56]2)[CH:57]2[CH2:58][CH2:59]2)[cH:60]1.CS(=O)(=O)[O:101][CH2:1][C:2]1([CH2:3][C:4]([O:5][CH3:6])=[O:7])[CH2:8][CH2:9]1.[H-:301].[Na+]', r'[CH2:1]([C:2]1([CH2:3][C:4]([O:5][CH3:6])=[O:7])[CH2:8][CH2:9]1)[O:18][c:17]1[cH:16][c:15]([CH2:14][CH2:13][CH2:12][O:11][CH3:10])[cH:60][c:20]([CH2:21][N:22]([C:23](=[O:24])[C@H:25]2[CH2:26][N:27]([C:28](=[O:29])[O:30][C:31]([CH3:32])([CH3:33])[CH3:34])[CH2:35][CH2:36][C@@H:37]2[c:38]2[cH:39][cH:40][c:41]([O:42][CH2:43][CH2:44][O:45][c:46]3[c:47]([Cl:48])[cH:49][c:50]([CH3:51])[cH:52][c:53]3[Cl:54])[cH:55][cH:56]2)[CH:57]2[CH2:58][CH2:59]2)[cH:19]1', 'large_row720')"
