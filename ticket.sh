#!/bin/bash -x
###########################################################
# Script for launching gaussian03 jobs to the queue       #
# usage: qg03 xxx                                         #
# where xxx.com is the name of the input file             #
# This script will:                                       #
# 1) create a xxx.qsub file                               #
# 2) launch it                                            #
#                                                         #
# 1) will create a temporary file named tmp.q             #
#    that will be passed to the sed command to change     #
#    'inputfilehere' for xxx to obtain xxx.qsub           #
#    the contains of the tmp.q file can be modified       #
#    for other queue name, walltime, etc                  #
#                                                         #
#    the xxx.qsub file also defines information of local  #
#    directory (HERE), scratch directory (SCRATCH),etc    #
#    a directory named xxx will be created in the scratch #
#    directory to alocate temporary files and checkpoint  #
#    files.                                               #
#                                                         #
#    When finishing, temporary files will be removed.     #
#    If the job did not finished properly or if the       #
#    walltime was over before finishing the calculation   #
#    they must be moved manually.                         #
#                                                         #
# 2) will run the xxx.qsub file using the qsub command.   #
#    An xxx.log and xxx.err file will also be created     #
#    containing messages and error messages of the        #
#    calculation.                                         #
#                                                         #
# To restart a calculation: make sure the checkpoint file #
# is in the xxx directory inside the scratch directory    #
# and run qg03 xxx                                        #
#                                                         #
# When it finised: delete or move the directory xxx from  #
# the scratch directory                                   #
###########################################################
if [ $# -lt 1 ]
then
    echo 'Not enough arguments'
    exit 1
fi
#the text on the tmp.q file....:
echo '#!/bin/bash
#SBATCH -p SWAN
#SBATCH --nodes=1
#SBATCH --cpus-per-task=12
#SBATCH --time=30:00:00
#SBATCH --mail-type=ALL
file=inputfilehere
inpfile=${file}.gjf
outfile=${file}.out
HERE=$SLURM_SUBMIT_DIR
SCRATCH=/scratch/rd611/$SLURM_JOB_${file}
mkdir ${SCRATCH}
export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK
export GAUSS_EXEDIR=/usr/local/shared/gaussian/x86_64_sse4/16-B01/g16
export g16root=/usr/local/shared/gaussian/x86_64_sse4/16-B01
export PATH=/usr/local/shared/gaussian/x86_64_sse4/16-B01/g16:$PATH
export GAUSS_SCRDIR=$SCRATCH
exe=$GAUSS_EXEDIR/g16
cp ${HERE}/${inpfile}  $SCRATCH
cd $SCRATCH
#
# Write out some helpful info to the output file
#
echo "Starting job $SLURM_JOBID"
echo
echo "SLURM assigned me this node:"
srun hostname
echo
ln -s $HERE/$outfile $SCRATCH/$outfile
srun $exe > $outfile < $inpfile
#cleaning when finished
mkdir ${HERE}/${file}
cp ${SCRATCH}/*.chk  $HERE/${file}/
rm -f ${SCRATCH}/*
cp $HERE/${file}/*.chk ${SCRATCH}/
rm -r ${HERE}/${file}
'>tmp.q
#create xxx.qsub file
sed "/inputfilehere/s//$1/g" tmp.q > $1.qsub
#remove temporary file tmp.q
rm tmp.q
echo "please delete the scratch directory:"
echo $SCRATCH
echo " when calculation is finished and checkpoint file is no longer needed"
#submit calculation to the queue
sbatch -o $1.log -e $1.err $1.qsub
