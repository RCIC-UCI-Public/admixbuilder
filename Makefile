## This Makefile is a high-level builder of all Admixes
REPOROOT = git@github.com:RCIC-UCI-Public
ADMIXES = biotools-admix buildlibs-admix buildtools-admix chemistry-admix conda-admix
ADMIXES += cuda-admix fileformats-admix foundation-admix gcc-admix
ADMIXES += mathlibs-admix perl-admix python-admix R-admix systools-admix tensorflow-admix
ADMIXES += parallel-admix pytorch-admix

ADMIXROOT = ..

ADMIXDIRS = $(patsubst, %, $(ADMIXROOT)%,$(ADMIXES))
PWD := $(shell pwd)
BUILDORDER = $(shell cat buildorder)


deplist.yaml:
	- /bin/rm $@
	for am in $(ADMIXES); do echo $$am; make -s -C $(ADMIXROOT)/$$am module-requires-provides >> $@; done 

buildall:
	- /bin/rm buildall.log
	( for admix in $(BUILDORDER); do                     \
	     echo "$$admix build start at `date`" >> $(PWD)/buildall.log; \
	     cd $(ADMIXROOT)/$$admix;                        \
	     make buildall &> $(PWD)/$$admix.log;            \
	     make -s install-admix &> $(PWD)/$$admix.install.log; \
	     cd $(PWD);                                      \
	     echo "$$admix build end at `date`" >> $(PWD)/buildall.log; \
	  done                                               \
        )
	
clone:
	for am in $(ADMIXES); do echo $$am; (cd ..; git clone $(REPOROOT)/$$am); done 


clean:
	- /bin/rm deplist.yaml
diag:
	echo $(ADMIXES)

