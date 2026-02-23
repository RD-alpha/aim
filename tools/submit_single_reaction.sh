#!/bin/bash
# One-liner SLURM submission for a single reaction
# Usage: ./submit_single_reaction.sh "SMILES_STRING" [product_smiles] [job_label]
# Example: ./submit_single_reaction.sh "CC(C)Br" "C" "grignard_test"

REACTANT="${1:-CC(C)Br}"
PRODUCT="${2:-C}"
JOB_LABEL="${3:-test_job}"
WALLTIME="${4:-12:50:00}"

sbatch <(cat << EOF
#!/bin/bash
#SBATCH -J ${JOB_LABEL}
#SBATCH -p CLUSTER
#SBATCH --nodes=1
#SBATCH --cpus-per-task=16
#SBATCH --time=${WALLTIME}
#SBATCH --mail-type=ALL
#SBATCH --signal=B:USR1@60

source ~/.bashrc
export PATH=\$HOME/.conda/envs/venv/bin:\$PATH

SCRATCH=/scratch/\$USER/\$SLURM_JOB_ID
mkdir -p \$SCRATCH
export SCRATCH

python -c "from run_parallel_config import run_parallel; run_parallel(r'${REACTANT}', r'${PRODUCT}', '${JOB_LABEL}')"
EOF
)

echo "Submitted job: ${JOB_LABEL}"
