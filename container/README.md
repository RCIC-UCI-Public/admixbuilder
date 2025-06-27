Setting up For Singularity-based builds
=======================================

On the physical host
--------------------

1. (optional). Setup a singularity cache directory (instead of the default in the User's home directory). 
   The file `singularity.sh` can be installed in the `/etc/profile.d` directory. Adjust location as desired.

2. Build the baseline singularity container. This only needs to be done once for each release
   ```bash
   export RELEASE=9.5 
   singularity build --fakeroot admixbuilder-${RELEASE}.sif admixbuilder.recipe  
   ```
3. (Optional) install base containter image a common area so that only one copy is required. On builder-l16, this is located
   in ``/opt/singularity/containers`` and is the environment variable CONTAINERS:

   ```bash
   install -m 664 --group builders admixbuilder-${RELEASE}.sif ${CONTAINERS}
   ``` 

Using a container
-----------------

The base container is read-only. To build/install packages and simulate a fully-virtualized build host,
an overlay directory is needed. 

There are two supported methods for overlays: subdirectory and single image.
Since building RPMS also requires installation of RPMS within the container, the builder must be "root" within the container.
There are two methods of achieving this:

  1. `sudo singularity shell ...`
   
     Really, the only supported method for building using yaml2rpm is to use a subdirectory structure and `sudo`.
  2. `singularity shell --fakeroot`

      To use option 2, only a single image (e.g. via `dd`) is supported, and that still has other issues for mappings.

Builder-l16 configuration
-------------------------

On `builder-l16`, there are six, 3.8TB nvme drives mounted as `/disks/nvme[0-3,5,6]`. Within
each of those directories there exists the subdirectory `builders/${USER}`, for each member of the builders unix group.

Each builder can manage there own naming within there infrastructure and create a separate zfs slice for each build release:

```bash
   zfs list
   NAME                                          USED  AVAIL     REFER  MOUNTPOINT
   nvme3                                         661G  2.73T      661G  /disks/nvme3
   nvme5                                        1.29T  2.09T      100K  /disks/nvme5
   nvme5/builders                               1.29T  2.09T      104K  /disks/nvme5/builders
   nvme5/builders/npw                           1.29T  2.09T      124K  /disks/nvme5/builders/npw
   nvme5/builders/npw/basebuild-9.6              305G  2.09T      305G  /disks/nvme5/builders/npw/basebuild-9.6 
   nvme5/builders/ppapadop                        96K  2.09T       96K  /disks/nvme5/builders/ppapadop
   nvme6                                        1.90T  1.47T      100K  /disks/nvme6
   nvme6/builders                               1.90T  1.47T      112K  /disks/nvme6/builders
   nvme6/builders/npw                            100K  1.47T      100K  /disks/nvme6/builders/npw
   nvme6/builders/ppapadop                      1.90T  1.47T     37.7M  /disks/nvme6/builders/ppapadop
   nvme6/builders/ppapadop/basebuild-9.5n        691G  1.47T      598G  /disks/nvme6/builders/ppapadop/basebuild-9.5n
   nvme6/builders/ppapadop/basebuild-9.6         630G  1.47T      630G  /disks/nvme6/builders/ppapadop/basebuild-9.6
   ...
```
To create a new zfs slice, ad root on ``builder-l16`` host:
   ```bash
      zfs create nvme5/builders/npw/basebuild-9.6
   ```

This gives an example for builder `ppapadop` on `nvme0` and an overlay named `basebuild-9.5`. 
The bind options provde bindings from the physical host: 

```bash
export RELEASE=9.5
export NVME=nvme6
export MYOVERLAY="/disks/${NVME}/builders/${USER}/basebuild-${RELEASE}"
export BASECONTAINER=${CONTAINERS}/admixbuilder-${RELEASE}.sif
if [ ! -d $MYOVERLAY ]; then mkdir -p $MYOVERLAY; fi
sudo singularity shell --containall \
                       --bind=/opt/data/opt:/data/opt:ro,/dev/fuse:/dev/fuse \
                       --cpus=16 --overlay ${MYOVERLAY} ${BASECONTAINER} 
```


First Build of yaml2rpm inside of a container
=============================================

```bash
sudo singularity shell --containall \
                       --bind=/opt/data/opt:/data/opt:ro,/dev/fuse:/dev/fuse \
                       --cpus=16 --overlay ${MYOVERLAY} ${BASECONTAINER}
bash -l
cd /export/repositories/
git clone https://github.com/RCIC-UCI-Public/yaml2rpm
cd yaml2rpm
./first-build.sh 
```

The above git command will give read-only repository

Notes:
1. Can clone *writeable* git repositories with an appropriate ssh key
   
   ```bash
   ssh-agent $SHELL
   ssh-add <path-to-ssh-key>
   git clone git@github.com:RCIC-UCI-Public/yaml2rpm
   ```

2. From the physical host, one can see the generated RPMS

   ```bash
   sudo ls -l $MYOVERLAY/upper/export/repositories/yaml2rpm/RPMS/*    
   yaml2rpm/RPMS/noarch:
   total 789
   -rw-r--r--. 1 root root   8283 Jun 27 10:34 bin-python-3-2.noarch.rpm
   -rw-r--r--. 1 root root 737530 Jun 27 10:34 python-future-0.18.2-1.noarch.rpm

   yaml2rpm/RPMS/x86_64:
   total 640
   -rw-r--r--. 1 root root 190395 Jun 27 10:34 python-ruamel-yaml-0.16.12-1.x86_64.rpm
   -rw-r--r--. 1 root root 150352 Jun 27 10:35 python-ruamel-yaml-clib-0.2.2-1.x86_64.rpm
   -rw-r--r--. 1 root root   6774 Jun 27 10:35 rcic-dev-repo-0.9-1.x86_64.rpm
   -rw-r--r--. 1 root root   8478 Jun 27 10:35 rcic-module-path-1.0-23.x86_64.rpm
   -rw-r--r--. 1 root root   6903 Jun 27 10:35 rcic-module-support-2-27.x86_64.rpm
   -rw-r--r--. 1 root root  39967 Jun 27 10:34 rocks-devel-9.0-18.x86_64.rpm
   -rw-r--r--. 1 root root  38116 Jun 27 10:35 yaml2rpm-2-43.x86_64.rpm

   ```

3. If you want to copy a file *into* the overlay from the physical host (e.g. an ssh key), then copy a file
   to the overlay. e.g.

   ```bash
   sudo cp ~ppapadop/id_ppapadop_git $MYOVERLAY/upper/export/repositories
   ```
Superbuild
==========

Clone ``admixbuilder`` repo and start the superbuild script:

```bash
   git clone git@github.com:RCIC-UCI-Public/admixbuilder
   cd admixbuilder/
   nohup ./superbuild.sh &> out-superbuild &
```

If you see errors right away similar to the following:
   ```txt
   The authenticity of host 'github.com (140.82.116.4)' can't be established.
   ED25519 key fingerprint is SHA256:+DiY3wvvV6TuJJhbpZisF/zLDA0zPMSvHdkr4UvCOqU.
   This key is not known by any other names
   Are you sure you want to continue connecting (yes/no/[fingerprint])?
   ```

Cancel the build, add ssh key for the github host, and restart superbuild anew:

   ```bash
     ssh-keyscan 140.82.116.4 >> ~/.ssh/known_hosts
     nohup ./superbuild.sh &> out-superbuild &
   ```

The ``superscript.sh``  starts a parallel build on defined groups of admixes (definition is a separate topic).
For each admix repo defined in the parallel build there will be 2 log files, for example:
   - bioconda-admix.install.log    
   - bioconda-admix.log     
