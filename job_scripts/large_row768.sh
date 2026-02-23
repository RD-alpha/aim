#!/bin/bash
#! SLURM job script for benchmark_large_row768
#! Based on ps.qsub template
#!
#SBATCH -J benchmark_large_row768
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
python -c "from run_parallel_config import run_parallel; run_parallel(r'[NH2:17][CH2:18][CH2:19][O:20][CH2:21][CH2:22][O:23][CH2:24][CH2:25][NH:26][C:27](=[O:28])[CH2:29][CH2:30][CH2:31][CH2:32][CH2:33][CH2:34][CH2:35][CH2:36][CH2:37][CH2:38][S:39][C:40]([c:41]1[cH:42][cH:43][cH:44][cH:45][cH:46]1)([c:47]1[cH:48][cH:49][cH:50][cH:51][cH:52]1)[c:53]1[cH:54][cH:55][cH:56][cH:57][cH:58]1.[OH:101][C:1](=[O:2])[CH2:3][NH:4][c:5]1[cH:6][cH:7][c:8]([N+:9](=[O:10])[OH:11])[cH:12][c:13]1[N+:14](=[O:15])[OH:16].[N:301](=[C:302]=[N:303]C1CCCCC1)C2CCCCC2', r'[C:1](=[O:2])([CH2:3][NH:4][c:5]1[cH:6][cH:7][c:8]([N+:9](=[O:10])[OH:11])[cH:12][c:13]1[N+:14](=[O:15])[OH:16])[NH:17][CH2:18][CH2:19][O:20][CH2:21][CH2:22][O:23][CH2:24][CH2:25][NH:26][C:27](=[O:28])[CH2:29][CH2:30][CH2:31][CH2:32][CH2:33][CH2:34][CH2:35][CH2:36][CH2:37][CH2:38][S:39][C:40]([c:41]1[cH:42][cH:43][cH:44][cH:45][cH:46]1)([c:47]1[cH:48][cH:49][cH:50][cH:51][cH:52]1)[c:53]1[cH:54][cH:55][cH:56][cH:57][cH:58]1', 'large_row768')"
