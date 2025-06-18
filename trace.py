#!/usr/bin/env python
from __future__ import print_function
import re
import sys
import os
import ruamel.yaml
import argparse
from datetime import date
from collections import OrderedDict

class Package(object):
    def __init__(self, name, value, allpkgs):
        # info about package
        self.pkgname = name
        self.provides = value['provides']  # is a list with a single item or None
        self.requires = value['requires']  # is a list with 0 or more items or None
        self.category = value['category']  # string or False

        if self.requires is None:
            self.requires = []
        if self.provides is None:
            self.provides = []

        # for a module add the rpm of the package to requirements
        if self.category: 
            pkgname = name.strip("-module")
            if pkgname in allpkgs:
                self.requires.append(pkgname)

    def printPackage(self):
        # for debugging 
        print("DEBUG %s provides" % self.pkgname, self.provides)
        print("DEBUG %s requires" % self.pkgname, self.requires)

    def getPkgProvides(self):
        return self.provides

    def getPkgRequires(self):
        return self.requires

class Admix(object):
    def __init__(self,name,info,created):
        # info about admix
        self.name = name
        self.allrequires = []
        self.allprovides = []
        self.created = created
        self.packages = {}

        self.processInfo(info)

    def processInfo(self,content):
        allpkgs = content.keys()
        self.mapname = {}
        for key, value in content.items():
            if key == "system":
                continue     # skip entries for "system:"
            self.packages[key] = Package(key, value, allpkgs)
            pkgprovides = self.packages[key].getPkgProvides()

            # special cases where provides include libs, perl subpackages. etc
            pkgstr = ''.join(pkgprovides)
            if pkgstr.find("(") > 0:
                pkgprovides.insert(0, key)

            self.allprovides += pkgprovides
            self.mapname[pkgprovides[0]] = key 
            self.allrequires += self.packages[key].getPkgRequires()

        # dedup
        self.allrequires = list(OrderedDict.fromkeys(self.allrequires))
        self.allprovides = list(OrderedDict.fromkeys(self.allprovides))

    def nameRemap(self, mapping):
        # remap provides
        update_p = []
        for i in self.allprovides:
            try:
                update_p.append(mapping[i]) # remap
            except:
                update_p.append(i)        
        self.allprovides = update_p

        # remap requires
        update_r = []
        for i in self.allrequires:
            try:
                update_r.append(mapping[i]) # remap
            except:
                update_r.append(i)         
        self.allrequires = update_r

    def getNumber(self):
        return len(self.mapname)

    def getMap(self):
        return self.mapname

    def getProvides(self):
        return self.allprovides

    def getNodeName(self):
        return self.name

    def getAdmixPackages(self):
        return self.packages


class Content:
    def __init__(self, args=None):
        # yaml file parser and main processor of its info 
        self.prog = args[0]
        self.args = args[1:]     # command line arguments

        self.parseArg()

    def parseArg(self):
        self.infile = "depinfo.yaml"

        description = "Show all packages by admix that depend on a given package name\n"
        helppkgname = "Package name for which to show dependecies.\n"
        helppkgname += "Can be specified as a partial name: gcc/6 or gcc_8"
        helpdefaults = "Yaml file that has requires, provides, category\n" 
        helpdefaults += "info for all packages. Default is %s\n" % self.infile

        parser = argparse.ArgumentParser(description=description, formatter_class=argparse.RawTextHelpFormatter)
        # optional  argument
        parser.add_argument("-d", "--defaults", dest="infile", default=self.infile, help=helpdefaults)
        # required positional argument
        parser.add_argument("pkgname",  action="store", help=helppkgname)

        args = parser.parse_args()
        if not os.path.isfile(args.infile):
            sys.stderr.write("Input yaml file %s does not exist\n" % args.infile)
            sys.exit(-1)

        self.infile = args.infile
        self.search = args.pkgname
        return

    def readYaml(self):
        f = open(self.infile)
        self.yaml = ruamel.yaml.YAML(typ='safe', pure=True)
        contents = self.yaml.load(f) # ruamel.yaml automatically cheks for duplicates

        # NOTE: as of pyyaml 5.* the line below gives a warning.
        #       contents = yaml.load(f)
        # works with pyyaml 5.* edited line:
        #       contents = yaml.load(f,Loader=yaml.FullLoader)

        try:
           created = contents['created']
           del contents['created']
        except:
           created = str(date.today())
        self.yamlcontent = contents
        self.created = created

    def processYamlInfo(self):
        self.admixes = {}   # for admix nodes
        self.map = {}       # mapping form module/pkg  name to rpm name
        self.pkgnumber = 0  # number of packages in yaml file  
        for admixname, admixinfo in self.yamlcontent.items():
            self.admixes[admixname] = Admix(admixname,admixinfo,self.created)
            self.map.update(self.admixes[admixname].getMap())
            self.pkgnumber += self.admixes[admixname].getNumber()

        # remap requires and provides to rpm packages names
        for key, node in self.admixes.items():
            self.admixes[key].nameRemap(self.map)
            
    def Trace(self):
        self.found = {}   # packages by admix providing search criteria names
        self.update = {}  # packages by admix to update if search criteria matches

        # remap search items to provider rpm names
        self.needles = []
        for key, value in self.map.items():
            if key.find(self.search) > -1:
                self.needles.append(value)

        for key, node in self.admixes.items():
            admixname = node.getNodeName()
            provides = node.getProvides()

            # find waht packages provide search criteria name
            for p in provides:
                for n in self.needles:
                    if p.find(n) > -1: 
                        try:
                           self.found[admixname].append(p)
                        except:
                           self.found[admixname] = [p]

            # packages whose requires match search criteria names
            pkgs = node.getAdmixPackages()
            for key, val in pkgs.items():
                requires = val.getPkgRequires()
                for r in requires:
                    try: 
                        rr = self.map[r]
                        for n in self.needles:
                            if rr.find(n) > -1 :
                                try:
                                   self.update[admixname].append(key)
                                except:
                                   self.update[admixname] = [key]
                    except:
                        # issue warning if package requirement is an orphan
                        print ("WARNING: none of packages provide", r)

        # order found packages
        for key, val in self.found.items():
            reorder = list(OrderedDict.fromkeys(val))
            self.found[key] = reorder

        # sort and dedup need to udpate packages per admix
        for name, deplist in self.update.items():
            self.update[name] = sorted(set(deplist))

    def printDependencies(self):
        if not self.found:
            print ("\nPackage name containing '%s' is not found" % self.search)
            return

        for key, value in self.found.items():
            print ("Provider: %s" % key)
            for pkg in value: 
                print ("    %s" % pkg)

        if not self.update:
            print ("\nNo dependencies found")
            return

        print ("\nNeed to rebuild packages")
        for item in sorted(self.update.items()):
            admixname = item[0]
            pkglist = item[1]
            print ("\n%s:" % admixname)
            for pkg in pkglist: 
                print ("    %s" % pkg)

    def run(self):
        self.readYaml()
        self.processYamlInfo()
        self.Trace()
        self.printDependencies()

#####################################################
if __name__ == "__main__":
    app = Content(sys.argv)
    app.run()
