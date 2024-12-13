#!/bin/bash

# Use build log files to compare number of RPMS made vs number of RPM installed
# This is a very first approximation as the numbers can be different and correct.
# RPMs made > RPMs installed as in gcc-admix: there are bootstrap RPMS made but not installed
# RPMs made < RPMs installed as in conda-admix: includes "system:" packages

ALL=`cat buildorder | grep -v "#"`

for i in  $ALL; do
    BLOG=$i.log
    ILOG=$i.install.log
    echo $i
    if [ -f $BLOG ]; then
        RPMS=`grep Wrote: $BLOG | wc -l`
        echo  "    RPMS      "  $RPMS
    else
        echo "    No $BLOG file"
    fi
    if [ -f $ILOG ]; then
        ALREADY=`grep already $ILOG | wc -l`
        INSTALLING=`grep " -roll " $ILOG | wc -l`
        INST=`python -c "print($ALREADY+$INSTALLING)"`
        echo  "    Installed " $INST 
    else
        echo "    No $ILOG file"
    fi
done
