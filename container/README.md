*  Setting up For Singularity-based builds *

On the physical host:

1. (optional). Setup a singularity cache directory (instead of the default in the User's home directory). 
   The file `singularity.sh` can be installed in the `/etc/profile.d` directory. Adjust location as desired.

2. Build the baseline singularity container. This only needs to be done once for each release
   ```
   export RELEASE=9.5 
   singularity build --fakeroot admixbuilder-${RELEASE}.sif admixbuilder.recipe  
   ```
3. (Optional) install base containter image a common area so that only one copy is required. On builder-l16, this is located
   in `/opt/singularity/containers` and is the environment variable CONTAINERS
   ```install -m 664 --group builders admixbuilder-${RELEASE}.sif ${CONTAINERS}``` 


When using a container, the base container is read-only. To build/install packages and simulate a fully-virtualized build host,
an overlay directory is needed. 

There are two supported methods for overlays: subdirectory and single image.
Since building RPMS also requires installation of RPMS within the container, the builder must be "root" within the container.
There are two methods of achieving this

1. `sudo singularity shell ...`
2. `singularity shell --fakeroot

To use option 2, only a single image (e.g. via `dd`) is supported, and that still has other issues for mappings. Really, the only
supported method for building using yaml2rpm is to use a subdirectory structure and `sudo`.

*Builder-l16 configuration*
On `builder-l16`, there are six, 3.8TB nvme drives mounted as `/disks/nvme[0-3,5,6]`. Within
each of those directories there exists the subdirectory `builders/${USER}`, for each member of the builders unix group.

Each builder can manage there own naming within there infrastructure.  This gives an example for builder
`ppapadop` on `nvme0` and an overlay named `basebuild-9.5`.

```
export RELEASE=9.5
export NVME=nvme6
export MYOVERLAY="/disks/${NVME}/builders/${USER}/basebuild-${RELEASE}"
export BASECONTAINER=${CONTAINERS}/admixbuilder-${RELEASE}.sif
if [ ! -d $MYOVERLAY ]; then mkdir -p $MYOVERLAY; fi
sudo singularity shell --containall --overlay ${MYOVERLAY} ${BASECONTAINER} 
```


*First Build of yaml2rpm inside of a container*

```
sudo singularity shell --containall --overlay ${MYOVERLAY} ${BASECONTAINER}
bash -l
cd /export/repositories/
git clone https://github.com/RCIC-UCI-Public/yaml2rpm
cd yaml2rpm
./first-build.sh 
```

Notes:
1. Can clone *writeable* git repositories with an appropriate ssh key.

2. From the physical host, one can see the generated RPMS
`sudo ls -l $MYOVERLAY/upper/export/repositories/yaml2rpm/RPMS/x86_64`

```
total 595
-rw-r--r--. 1 root root 189413 Mar  4 13:53 python-ruamel-yaml-0.16.12-1.x86_64.rpm
-rw-r--r--. 1 root root 150430 Mar  4 13:53 python-ruamel-yaml-clib-0.2.2-1.x86_64.rpm
-rw-r--r--. 1 root root   6780 Mar  4 13:53 rcic-dev-repo-0.9-1.x86_64.rpm
-rw-r--r--. 1 root root   8480 Mar  4 13:53 rcic-module-path-1.0-22.x86_64.rpm
-rw-r--r--. 1 root root  11475 Mar  4 13:53 rcic-module-support-2-24.x86_64.rpm
-rw-r--r--. 1 root root  32607 Mar  4 13:53 yaml2rpm-2-26.x86_64.rpm
```

3. If you want to copy a file *into* the overlay from the physical host (e.g. an ssh key), then copy a file
to the overlay. e.g.

```
sudo cp ~ppapadop/id_ppapadop_git $MYOVERLAY/upper/export/repositories
```
