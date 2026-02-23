#!/bin/bash
#! SLURM job script for benchmark_large_row611
#! Based on ps.qsub template
#!
#SBATCH -J benchmark_large_row611
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
python -c "from run_parallel_config import run_parallel; run_parallel(r'CC(C)(C)[Si:101](C)(C)[O:1][c:2]1[cH:3][c:4]([O:5][CH2:6][CH3:7])[cH:8][c:9]([CH:10]([NH:11][c:12]2[cH:13][cH:14][c:15]3[c:16]([N:17]([C:18](=[O:19])[O:20][C:21]([CH3:22])([CH3:23])[CH3:24])[C:25](=[O:26])[O:27][C:28]([CH3:29])([CH3:30])[CH3:31])[n:32][cH:33][cH:34][c:35]3[cH:36]2)[c:37]2[n:38][c:39](-[c:40]3[cH:41][cH:42][cH:43][cH:44][cH:45]3)[cH:46][n:47]2[C:48]([c:49]2[cH:50][cH:51][cH:52][cH:53][cH:54]2)([c:55]2[cH:56][cH:57][cH:58][cH:59][cH:60]2)[c:61]2[cH:62][cH:63][cH:64][cH:65][cH:66]2)[c:67]1[F:68].[F-:301]', r'[OH:1][c:2]1[cH:3][c:4]([O:5][CH2:6][CH3:7])[cH:8][c:9]([CH:10]([NH:11][c:12]2[cH:13][cH:14][c:15]3[c:16]([N:17]([C:18](=[O:19])[O:20][C:21]([CH3:22])([CH3:23])[CH3:24])[C:25](=[O:26])[O:27][C:28]([CH3:29])([CH3:30])[CH3:31])[n:32][cH:33][cH:34][c:35]3[cH:36]2)[c:37]2[n:38][c:39](-[c:40]3[cH:41][cH:42][cH:43][cH:44][cH:45]3)[cH:46][n:47]2[C:48]([c:49]2[cH:50][cH:51][cH:52][cH:53][cH:54]2)([c:55]2[cH:56][cH:57][cH:58][cH:59][cH:60]2)[c:61]2[cH:62][cH:63][cH:64][cH:65][cH:66]2)[c:67]1[F:68]', 'large_row611')"
