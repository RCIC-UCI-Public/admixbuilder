#!/bin/bash
# Basic system prep for Rocky 8
# Get yumdownloader
yum -y install yum-utils  

# enable the powertools repo
yum-config-manager --enable powertools

