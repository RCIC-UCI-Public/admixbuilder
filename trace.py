#!/usr/bin/env python
from __future__ import print_function
import re
import sys
import os
import ruamel.yaml
import argparse
from datetime import date
from collections import OrderedDict

class Admix(object):
    def __init__(self,name,info,created):
        self.name = name
        self.requires = []
        self.provides = []
        self.requires_category = {}
        self.provides_category = {}
        self.created = created
        self.packages = {}

        self.processInfo(info)

    def processInfo(self,content):
        for key, value in content.items():
            self.packages[key] = value
            provides = value['provides']  # is a list with a single item or None
            requires = value['requires']  # is a list with 0 or more items or None
            category = value['category']  # string or False
            if provides:
                provides = self.checkExceptions(provides)
                self.provides += provides
            if requires:
                self.requires += requires
            if category: 
                if category in self.provides_category.keys():
                    if provides[0] not in self.provides_category[category]:
                        self.provides_category[category] += provides
                else:
                    self.provides_category[category] = provides
 
                if requires: 
                    if category in self.requires_category.keys():
                        self.requires_category[category] += requires
                    else:
                        self.requires_category[category] = []
                        for r in requires:
                            self.requires_category[category].append (r)
                        # !!! WRONG !!! changes the underlying dictionary requires for a module
                        #self.requires_category[category] = requires

        self.requires = list(OrderedDict.fromkeys(self.requires))
        self.provides = list(OrderedDict.fromkeys(self.provides))


    def checkExceptions(self,modname):
        # this is a temp way to eliminate pytorch-cuda names from provides.
        # we use pytorch-cuda in module logger and in RPM name and  provides but
        # the users only se a single module pytorch/<version>
        # cuda-enabled version is installed on cuda nodes.
        self.exceptions = {"pytorch-cuda":"pytorch"}
        update = modname[0]
        for origName, changedName in self.exceptions.items():
            if modname[0].find(origName) == 0:
                update = modname[0].replace(origName,changedName)
        return [update]

    def getRequires(self):
        return self.requires

    def getProvides(self):
        return self.provides

    def getNodeName(self):
        return self.name


class Content:
    def __init__(self, args=None):
        self.prog = args[0]
        self.args = args[1:]     # command line arguments

        self.parseArg()

    def parseArg(self):
        self.infile = "depinfo.yaml"

        description = "Show all packages by admix that depend on a given package"
        helpdefaults = "specify yaml file to use. If none is provided, use %s\n" % self.infile
        helpdefaults += "that has requires, provides, category info for all packages."

        parser = argparse.ArgumentParser(description=description, formatter_class=argparse.RawTextHelpFormatter)
        # optional  argument
        parser.add_argument("-d", "--defaults", dest="infile", default=self.infile, help=helpdefaults)
        # required positional argument
        parser.add_argument("pkgname",  action="store", help="package name for which to show dependecies")

        args = parser.parse_args()
        if not os.path.isfile(args.infile):
            sys.stderr.write("Input yaml file %s does not exist\n" % args.yamlfile)
            sys.exit(-1)

        self.infile = args.infile
        self.search = args.pkgname
        return

    def readYaml(self):
        f = open(self.infile)
        self.yaml = ruamel.yaml.YAML(typ='safe', pure=True)
        admixes = self.yaml.load(f)

        # as of pyyaml 5.* the line below gives a warning.
        # need to use either the second line below or opt
        # for ruamel.yaml above which also checks for duplicates in yaml
        # original line : admixes = yaml.load(f)
        # works with pyyaml 5.* edited line:  admixes = yaml.load(f,Loader=yaml.FullLoader)

        try:
           created = admixes['created']
           del admixes['created']
        except:
           created = str(date.today())
        self.yamlcontent = admixes
        self.created = created

    def processYamlInfo(self):
        self.nodes = [] # for admix nodes
        for admixname, admixinfo in self.yamlcontent.items():
            self.nodes.append(Admix(admixname,admixinfo,self.created))

    def Trace(self):
        self.found = {}
        self.dependentAdmixes = []
        for node in self.nodes:
            admixname = node.getNodeName()
            provides = node.getProvides()
            for p in provides:
                if p.find(self.search) == 0:
                    try:
                        self.found[admixname].append (p)
                    except:
                        self.found[admixname] = [p]
            requires = node.getRequires()
            for r in requires:
                if r.find(self.search) == 0:
                    self.dependentAdmixes.append(admixname)

        self.update = {}
        for providerAdmix, providerMods in self.found.items():
            for admixname in self.dependentAdmixes:
                admixinfo = self.yamlcontent[admixname] 
                for key, value in admixinfo.items():
                    reqs = value['requires'] 
                    if not reqs: continue
                    for r in reqs:
                        if r in providerMods:
                            try: 
                                self.update[admixname].append(key)
                            except: 
                                self.update[admixname] = [key]
        self.printDependencies()

    def printDependencies(self):
        if not self.found:
            print ("\nPackage name containing '%s' is not found" % self.search)
            return

        for key, value in self.found.items():
            print ("Provider: %s" % key)
            for pkg in value: 
                print ("    module %s" % pkg)

        if not self.update:
            print ("\nNo dependencies found")
            return

        print ("\nNeed to rebuild packages")
        for admixname, pkglist in self.update.items():
            print ("\n%s:" % admixname)
            for pkg in pkglist: 
                print ("    %s" % pkg)


    def run(self):
        self.readYaml()
        self.processYamlInfo()
        self.Trace()

#####################################################
if __name__ == "__main__":
    app = Content(sys.argv)
    app.run()
