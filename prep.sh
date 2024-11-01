#!/bin/bash
# Basic system prep for Rocky 8/9
MAJOR=$(cat /etc/redhat-release | sed 's/.*release \([0-9]\+\).*/\1/')
# Get yumdownloader
yum -y install yum-utils  

# enable the powertools repo

if [ "$MAJOR" == "8" ]; then 
    echo "Enabling powertools yum repo"
    yum-config-manager --enable powertools
fi
# enable the crb repo
if [ "$MAJOR" == "9" ]; then 
    echo "Enabling powertools crb repo"
    yum-config-manager --enable crb
fi


