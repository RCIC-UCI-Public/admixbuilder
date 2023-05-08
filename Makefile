## This Makefile is a high-level builder of all Admixes
REPOROOT = git@github.com:RCIC-UCI-Public
CRSPDIR = /mnt/crsp/RPMS.CURRENT
ADMIXES = yaml2rpm biotools-admix buildlibs-admix buildtools-admix chemistry-admix conda-admix
ADMIXES += cuda-admix fileformats-admix foundation-admix gcc-admix
ADMIXES += mathlibs-admix perl-admix python-admix R4-admix systools-admix tensorflow-admix
ADMIXES += pytorch-admix
ADMIXES += bioconda-admix nfsapps-admix julia-admix simulations-admix
ADMIXES += rust-admix genomics-admix 
ADMIXES += imaging-admix 

ADMIXROOT = ..
ANSIBLEDIR = playbooks

ADMIXDIRS = $(patsubst, %, $(ADMIXROOT)%,$(ADMIXES))
PWD := $(shell pwd)
BUILDORDER = $(shell cat buildorder)

DOTFILES = dot-buildorder dot-byadmix dot-bycategory

.PHONY: force

depinfo.yaml:
	- /bin/rm $@
	echo "### Scanning admixes for module-info ###"
	for am in $(ADMIXES); do echo $$am; make -s -C $(ADMIXROOT)/$$am module-info >> $@; done
	echo "created: $$(date +%F)" >> $@

dot: depinfo.yaml
	./depend.py 

dotpdf:
	( for df in $(DOTFILES); do					\
		if [ -f $$df ]; then dot -Tpdf $$df -o $$df.pdf; fi ;	\
	  done								\
        )
dotpng:
	( for df in $(DOTFILES); do					\
		if [ -f $$df ]; then dot -Tpng $$df -o $$df.png; fi ;	\
	  done								\
        )


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
	
clone: force
	for am in $(ADMIXES); do echo $$am; (cd $(ADMIXROOT); git clone $(REPOROOT)/$$am); done 

status push pull: force
	for am in $(ADMIXES); do echo $$am; (cd $(ADMIXROOT)/$$am; git $@); done 

rpmcopy: force
	for am in $(ADMIXES); do echo $$am; ( 					\
		if [ ! -d $(CRSPDIR)/$$am ]; then mkdir $(CRSPDIR)/$$am; fi ; \
		cd $(ADMIXROOT)/$$am; find RPMS -name '*rpm' > $$am.rpms; /bin/cp --preserve=timestamps $$(cat $$am.rpms) $(CRSPDIR)/$$am) done 


download:
	for am in $(ADMIXES); do echo $$am; make -C $(ADMIXROOT)/$$am download; sleep 300;  done

clean:
	- /bin/rm deplist.yaml
diag:
	echo $(ADMIXES)

# Wildcard action to do something in all admix directories.
# example make "git checkout -b <branchname>"

%:
	for am in $(ADMIXES); do echo $$am; (cd $(ADMIXROOT)/$$am; $@); done 
