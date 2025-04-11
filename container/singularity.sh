# Setup a SINGULARITY CACHEDIR that is NOT in the user home area
# For builder-l16.rcic.uci.edu, there are per-user directories
export SINGULARITY_CACHEDIR=/opt/singularity/cache/${USER}
export CONTAINERS=/opt/singularity/containers

