#!/bin/bash
#! SLURM job script for benchmark_medium_row402
#! Based on ps.qsub template
#!
#SBATCH -J benchmark_medium_row402
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
python -c "from run_parallel_config import run_parallel; run_parallel(r'[CH3:10][O:11][C:12](=[O:13])[N:14]1[CH2:15][CH2:16][C@@H:17]([NH2:18])[C@@H:19]([CH3:20])[CH2:21]1.[OH:101][C:1]([c:2]1[nH:3][c:4]([CH3:5])[c:6]([Cl:7])[cH:8]1)=[O:9].[N:301](=[C:302]=[N:303]C1CCCCC1)C2CCCCC2', r'[C:1]([c:2]1[nH:3][c:4]([CH3:5])[c:6]([Cl:7])[cH:8]1)(=[O:9])[NH:18][C@@H:17]1[CH2:16][CH2:15][N:14]([C:12]([O:11][CH3:10])=[O:13])[CH2:21][C@@H:19]1[CH3:20]', 'medium_row402')"
