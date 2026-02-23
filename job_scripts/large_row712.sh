#!/bin/bash
#! SLURM job script for benchmark_large_row712
#! Based on ps.qsub template
#!
#SBATCH -J benchmark_large_row712
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
python -c "from run_parallel_config import run_parallel; run_parallel(r'[CH3:26][O:27][c:28]1[cH:29][cH:30][c:31]([C:32]2=[N:33][N:34]([CH:35]3[CH2:36][CH2:37][N:38]([C:39](=[O:40])[C@@H:41]([NH2:42])[CH2:43][c:44]4[cH:45][s:46][cH:47][n:48]4)[CH2:49][CH2:50]3)[C:51](=[O:52])[C@@H:53]3[CH2:54][CH2:55][CH2:56][CH2:57][C@H:58]23)[cH:59][c:60]1[O:61][CH3:62].[OH:101][C:1](=[O:2])[c:3]1[cH:4][nH:5][c:6]2[c:7](-[c:8]3[c:9]([O:10][CH2:11][CH:12]4[CH2:13][CH2:14]4)[cH:15][cH:16][c:17]4[c:18]3[O:19][CH2:20][O:21]4)[n:22][cH:23][n:24][c:25]12.[N:301](=[C:302]=[N:303]C1CCCCC1)C2CCCCC2', r'[C:1](=[O:2])([c:3]1[cH:4][nH:5][c:6]2[c:7](-[c:8]3[c:9]([O:10][CH2:11][CH:12]4[CH2:13][CH2:14]4)[cH:15][cH:16][c:17]4[c:18]3[O:19][CH2:20][O:21]4)[n:22][cH:23][n:24][c:25]12)[NH:42][C@H:41]([C:39]([N:38]1[CH2:37][CH2:36][CH:35]([N:34]2[N:33]=[C:32]([c:31]3[cH:30][cH:29][c:28]([O:27][CH3:26])[c:60]([O:61][CH3:62])[cH:59]3)[C@@H:58]3[C@H:53]([C:51]2=[O:52])[CH2:54][CH2:55][CH2:56][CH2:57]3)[CH2:50][CH2:49]1)=[O:40])[CH2:43][c:44]1[cH:45][s:46][cH:47][n:48]1', 'large_row712')"
