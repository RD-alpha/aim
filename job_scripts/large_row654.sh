#!/bin/bash
#! SLURM job script for benchmark_large_row654
#! Based on ps.qsub template
#!
#SBATCH -J benchmark_large_row654
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
python -c "from run_parallel_config import run_parallel; run_parallel(r'[CH3:27][O:28][c:29]1[cH:30][cH:31][c:32]([C:33]2=[N:34][N:35]([CH:36]3[CH2:37][CH2:38][N:39]([C:40](=[O:41])[C@H:42]([NH2:43])[CH2:44][c:45]4[cH:46][cH:47][c:48]([C:49]([CH3:50])([CH3:51])[CH3:52])[cH:53][cH:54]4)[CH2:55][CH2:56]3)[C:57](=[O:58])[C@@H:59]3[CH2:60][CH2:61][CH2:62][CH2:63][C@H:64]23)[cH:65][c:66]1[O:67][CH3:68].[OH:101][C:1]([c:2]1[c:3]2[n:4][cH:5][n:6][c:7](-[c:8]3[c:9]([O:10][CH2:11][CH:12]4[CH2:13][CH2:14]4)[cH:15][c:16]([O:17][CH3:18])[c:19]([F:20])[cH:21]3)[c:22]2[nH:23][c:24]1[CH3:25])=[O:26].[N:301](=[C:302]=[N:303]C1CCCCC1)C2CCCCC2', r'[C:1]([c:2]1[c:3]2[n:4][cH:5][n:6][c:7](-[c:8]3[c:9]([O:10][CH2:11][CH:12]4[CH2:13][CH2:14]4)[cH:15][c:16]([O:17][CH3:18])[c:19]([F:20])[cH:21]3)[c:22]2[nH:23][c:24]1[CH3:25])(=[O:26])[NH:43][C@@H:42]([C:40]([N:39]1[CH2:38][CH2:37][CH:36]([N:35]2[N:34]=[C:33]([c:32]3[cH:31][cH:30][c:29]([O:28][CH3:27])[c:66]([O:67][CH3:68])[cH:65]3)[C@@H:64]3[C@H:59]([C:57]2=[O:58])[CH2:60][CH2:61][CH2:62][CH2:63]3)[CH2:56][CH2:55]1)=[O:41])[CH2:44][c:45]1[cH:46][cH:47][c:48]([C:49]([CH3:50])([CH3:51])[CH3:52])[cH:53][cH:54]1', 'large_row654')"
