#!/bin/bash
# Create a distro from a set of RPMS in different directories
RPMSOURCE=${RPMSOURCE:/install/RPMS.ADMIXES}
DISTRODIR=${DISTRODIR:/install/RCIC}
TEMPDISTRO=$(mktemp -d admixdistro.XXX)

trap cleanup INT
function cleanup()
{
   if [ -d $TEMPDISTRO ] && [[ "$TEMPDISTRO" =~ ^admixdistro ]]; then
       /bin/rm -r $TEMPDISTRO
   fi
}                                    

echo "Copying RPMS to Temporary $TEMPDISTRO"
subdirs=$(find $RPMSOURCE -maxdepth 1 -type d -not -name . -not -name .git -not -name 'admixdistro*' | grep -v "$RPMSOURCE\$")

for sd in $subdirs; do
    echo "Copying RPMS from $sd to $TEMPDISTRO"
    find $sd -type f -name '*rpm' -exec install -m 644 {} $TEMPDISTRO \; -print
done

echo "Creating Yum Repo in $TEMPDISTRO"
pushd $TEMPDISTRO
createrepo .
popd
echo "...done"
