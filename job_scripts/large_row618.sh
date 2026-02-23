#!/bin/bash
#! SLURM job script for benchmark_large_row618
#! Based on ps.qsub template
#!
#SBATCH -J benchmark_large_row618
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
python -c "from run_parallel_config import run_parallel; run_parallel(r'[NH2:1][c:2]1[cH:3][c:4]([C:5](=[O:6])[NH:7][c:8]2[cH:9][c:10]([S:11](=[O:12])(=[O:13])[OH:14])[cH:15][c:16]3[cH:17][c:18]([S:19](=[O:20])(=[O:21])[OH:22])[cH:23][c:24]([S:25](=[O:26])(=[O:27])[OH:28])[c:29]23)[cH:30][c:31]([C:32](=[O:33])[NH:34][c:35]2[cH:36][c:37]([S:38](=[O:39])(=[O:40])[OH:41])[cH:42][c:43]3[cH:44][c:45]([S:46](=[O:47])(=[O:48])[OH:49])[cH:50][c:51]([S:52](=[O:53])(=[O:54])[OH:55])[c:56]23)[cH:57]1.[O:58]=[C:59]=[N:60][c:61]1[cH:62][cH:63][cH:64][c:65]([C:66]([F:67])([F:68])[F:69])[cH:70]1', r'[NH:1]([c:2]1[cH:3][c:4]([C:5](=[O:6])[NH:7][c:8]2[cH:9][c:10]([S:11](=[O:12])(=[O:13])[OH:14])[cH:15][c:16]3[cH:17][c:18]([S:19](=[O:20])(=[O:21])[OH:22])[cH:23][c:24]([S:25](=[O:26])(=[O:27])[OH:28])[c:29]23)[cH:30][c:31]([C:32](=[O:33])[NH:34][c:35]2[cH:36][c:37]([S:38](=[O:39])(=[O:40])[OH:41])[cH:42][c:43]3[cH:44][c:45]([S:46](=[O:47])(=[O:48])[OH:49])[cH:50][c:51]([S:52](=[O:53])(=[O:54])[OH:55])[c:56]23)[cH:57]1)[C:59](=[O:58])[NH:60][c:61]1[cH:62][cH:63][cH:64][c:65]([C:66]([F:67])([F:68])[F:69])[cH:70]1', 'large_row618')"
