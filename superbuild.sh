#!/bin/sh
GROUPSDIR=admixgroups
WORKFILES=$(ls ${GROUPSDIR} | sort)
echo $WORKFILES
# clean yum prior to building everything. 
yum clean all
for grp in ${WORKFILES}; do
	PARALLEL=$(wc -l ${GROUPSDIR}/${grp} | awk '{print $1}')
	echo "=== Start $grp at $(date) ==="
	cat ${GROUPSDIR}/${grp} | runparallel -p ${PARALLEL} --autoprefix run
	echo "=== Finished $grp at $(date) ==="
done
