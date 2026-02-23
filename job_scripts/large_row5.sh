#!/bin/bash
#! SLURM job script for benchmark_large_row5
#! Based on ps.qsub template
#!
#SBATCH -J benchmark_large_row5
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
python -c "from run_parallel_config import run_parallel; run_parallel(r'[CH3:6][C:7]1([CH3:8])[CH2:9][CH2:10][C:11]([CH2:12][N:13]2[CH2:14][CH2:15][N:16]([c:17]3[cH:18][cH:19][c:20]([C:21](=[O:22])[NH:23][S:24](=[O:25])(=[O:26])[c:27]4[cH:28][cH:29][c:30]([NH:31][CH2:32][CH:33]5[CH2:34][NH:35][CH2:36]5)[c:37]([N+:38](=[O:39])[OH:40])[cH:41]4)[c:42]([O:43][c:44]4[cH:45][n:46][c:47]5[nH:48][cH:49][cH:50][c:51]5[cH:52]4)[cH:53]3)[CH2:54][CH2:55]2)=[C:56]([c:57]2[cH:58][cH:59][c:60]([Cl:61])[cH:62][cH:63]2)[CH2:64]1.[O:101]=[C:1]([CH2:2][F:3])[CH2:4][F:5].[H+:301].[BH3-:302]C#N.[Na+]', r'[CH:1]([CH2:2][F:3])([CH2:4][F:5])[N:35]1[CH2:34][CH:33]([CH2:32][NH:31][c:30]2[cH:29][cH:28][c:27]([S:24]([NH:23][C:21]([c:20]3[cH:19][cH:18][c:17]([N:16]4[CH2:15][CH2:14][N:13]([CH2:12][C:11]5=[C:56]([c:57]6[cH:58][cH:59][c:60]([Cl:61])[cH:62][cH:63]6)[CH2:64][C:7]([CH3:6])([CH3:8])[CH2:9][CH2:10]5)[CH2:55][CH2:54]4)[cH:53][c:42]3[O:43][c:44]3[cH:45][n:46][c:47]4[nH:48][cH:49][cH:50][c:51]4[cH:52]3)=[O:22])(=[O:25])=[O:26])[cH:41][c:37]2[N+:38](=[O:39])[OH:40])[CH2:36]1', 'large_row5')"
