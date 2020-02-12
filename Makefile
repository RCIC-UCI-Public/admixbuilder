## This Makefile is a high-level builder of all Admixes
REPOROOT = git@github.com:RCIC-UCI-Public
CRSPDIR = /mnt/crsp/share/RPMS.CURRENT
ADMIXES = yaml2rpm biotools-admix buildlibs-admix buildtools-admix chemistry-admix conda-admix
ADMIXES += cuda-admix fileformats-admix foundation-admix gcc-admix
ADMIXES += mathlibs-admix perl-admix python-admix R-admix systools-admix tensorflow-admix
ADMIXES += parallel-admix pytorch-admix

ADMIXROOT = ..
ANSIBLEDIR = playbooks

ADMIXDIRS = $(patsubst, %, $(ADMIXROOT)%,$(ADMIXES))
PWD := $(shell pwd)
BUILDORDER = $(shell cat buildorder)

.PHONY: force

deplist.yaml: force
	- /bin/rm $@
	for am in $(ADMIXES); do echo $$am; make -s -C $(ADMIXROOT)/$$am module-requires-provides >> $@; done 

ansible: $(ANSIBLEDIR) force
	for am in $(ADMIXES); do echo $$am; make -s -C $(ADMIXROOT)/$$am ansible > $(ANSIBLEDIR)/$$am.yml; done 

$(ANSIBLEDIR):
	mkdir $@

buildall:
	- /bin/rm buildall.log
	( for admix in $(BUILDORDER); do                     \
	     echo "$$admix build start at `date`" >> $(PWD)/buildall.log; \
	     cd $(ADMIXROOT)/$$admix;                        \
	     make buildall &> $(PWD)/$$admix.log;            \
	     make -s YES=-y install-admix &> $(PWD)/$$admix.install.log; \
	     cd $(PWD);                                      \
	     echo "$$admix build end at `date`" >> $(PWD)/buildall.log; \
	  done                                               \
        )
	
clone:
	for am in $(ADMIXES); do echo $$am; (cd $(ADMIXROOT); git clone $(REPOROOT)/$$am); done 

status push pull:
	for am in $(ADMIXES); do echo $$am; (cd $(ADMIXROOT)/$$am; git $@); done 

rpmcopy:
	for am in $(ADMIXES); do echo $$am; ( 					\
		if [ ! -d $(CRSPDIR)/$$am ]; then mkdir $(CRSPDIR)/$$am; fi ; \
		cd $(ADMIXROOT)/$$am; find RPMS -name '*rpm' > $$am.rpms; /bin/cp $$(cat $$am.rpms) $(CRSPDIR)/$$am) done 



clean:
	- /bin/rm deplist.yaml
diag:
	echo $(ADMIXES)

