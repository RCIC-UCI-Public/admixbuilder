#!/usr/bin/env python
from __future__ import print_function
import re
import sys
import subprocess
import yaml
from datetime import date
from collections import OrderedDict

class Category(object):
    def __init__(self,name,created):
        self.name = name
        self.edges = []
        self.provides = []
        self.requires = []
        self.created = created;

        self.colorTitle = "dodgerblue4"    # graph title and legend
        self.colorLabelBG = "lightblue1"   # background of a category label
        self.colorModulesBG = "ghostwhite" # background of category modules
        self.labelheader = 'label=<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0">'
        self.labeltrailer = "</TABLE>>"
        self.namepattern = '<TR><TD bgcolor="%s"><font point-size="16" face="Times-Bold">%s</font></TD></TR>\n'

    def getCategoryName(self):
        return self.name

    def addCategoryProvides(self, mods):
        self.provides += mods

    def addCategoryRequires(self, mods):
        for m in mods:
            if m not in self.requires:
                self.requires.append(m)

    def addCategoryEdges(self,mods):
        for r in self.requires:
            modcat = mods[r] # module's category
            if modcat not in self.edges:
                self.edges.append(modcat)

    def getCategoryProvides(self):
        return self.provides

    def getCategoryEdges(self):
        return self.edges

    def orderCategoryModules(self):
        # rm duplicates
        self.requires = list(OrderedDict.fromkeys(self.requires))
        self.provides = list(OrderedDict.fromkeys(self.provides))

    def printCategoryDotHeader(self):
        title = "Software Modules by Category (%s)\n\nReusable  packages  created  with  yaml2rpm\nhttps://github.com/RCIC-UCI-Public/yaml2rpm\n\n" % self.created

        txt = "digraph G {\n"
        txt += '  size = "11,17";\n'
        txt += '  ranksep = "1";\n'
        txt += '  rankdir=TB;\n'
        txt += '  labelloc="t";\n  fontsize="24.0";\n'
        txt += '  fontcolor=%s;\n' % self.colorTitle
        txt += '  fontname="Times-Roman-Bold";\n'
        txt += '  fontsize=24;\n'
        txt += '  label="%s";\n' % title
        txt += self.printCategoryStaticFormat()

        return txt

    def printCategoryStaticFormat(self):
        # this is a result of palying with dot figure and aligning
        # categories so that they produce fewer adges and less white
        # space. Create an invisible top-bottom ancoring nodes for
        # fixing categories position via ranking

        txt = 'subgraph clusterLegend {\n'
        txt += '  rank=0\n'
        txt += '  constrain=false;\n'
        txt += '  label="Legend\n  \n"\n'
        txt += '  fontcolor=%s fontname="Numbus-Roman" fontsize=16\n' % self.colorTitle
        txt += '  color=%s\n' % self.colorTitle
        txt += '  labelloc = t\n\n'
        txt += '  nodeA [label="A", style="filled", color="%s", shape="box"];\n' % self.colorModulesBG
        txt += '  nodeB [label="B", style="filled", color="%s", shape="box"];\n' % self.colorModulesBG
        txt += '  nodeA -> nodeB [label="modules in A depend\n on  modules  in  B",labelloc=b];\n'
        txt += '  {rank=source; nodeA; nodeB};\n'
        txt += '};\n'

        txt += '{node [shape=plaintext, style=invis];  1 -> 2 -> 3 -> 4 [style=invis]}\n'
        txt += '{rank = same; 1; CHEMISTRY, ENGINEERING, GENOMICS, IMAGING, AI_LEARNING}\n'
        txt += '{rank = same; 2; TOOLS, BIOTOOLS}\n'
        txt += '{rank = same; 3; LANGUAGES, LIBRARIES}\n'
        txt += '{rank = same; 4; COMPILERS; PHYSICS; STATISTICS}\n'

        return txt


    def printCategoryDotTrailer(self):
        return "}\n"

    def printCategoryDotNotation(self):
        name = self.name.replace("-","_")
        txt = "\n## %s\n" % self.getCategoryName()
        txt += '%s [shape=plaintext, %s\n' % (name, self.labelheader)

        provlist='<TR><TD bgcolor="%s">\n  <BR/>' % self.colorModulesBG
        provides = self.getCategoryProvides()
        if provides is not None:
           provlist="%s%s" % (provlist, "\n  <BR/>".join(provides))
        provlist = provlist + "\n</TD></TR>\n"

        txt += '%s%s%s]' % (self.namepattern % (self.colorLabelBG,self.getCategoryName()), provlist, self.labeltrailer)

        edgenames = self.getCategoryEdges()
        for edge in edgenames:
            txt += "\n%s -> %s;" % (name, edge)
        txt += "\n"
        return txt

class Admix(object):
    def __init__(self,name,info,created):
        self.name = name
        self.edges = []
        self.requires = []
        self.provides = []
        self.requires_category = {}
        self.provides_category = {}
        self.created = created
        self.packages = []

        self.colorTitle = "dodgerblue4"     # graph title
        self.colorSpecs = "blue"            # for requires: and provides:
        self.colorLabelBG = "lightblue1"    # background of admix name
        self.colorProvidesBG = "ghostwhite" # background of proovided modules
        self.colorRequiresBG = "mintcream"  # background of required modules
        self.labelheader = 'label=<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0">'
        self.labeltrailer = "</TABLE>>"
        self.namepattern = '<TR><TD bgcolor="%s"><font point-size="16" face="Times-Bold">%s</font></TD></TR>\n'

        self.processInfo(info)

    def processInfo(self,info):
        for key, value in info.items():
            self.packages.append(key)
            provides = value['provides']  # is a list with a single item
            requires = value['requires']  # is a list with 0 or more items
            category = value['category']
            if provides:
                provides = self.checkExceptions(provides)
                self.provides += provides
            if requires:
                self.requires += requires
            if category: 
                if category in self.provides_category.keys():
                    # dont add if already present
                    if provides[0] not in self.provides_category[category]:
                        self.provides_category[category] += provides
                else:
                    self.provides_category[category] = provides

                if requires: 
                    if category in self.requires_category.keys():
                        self.requires_category[category] += requires
                    else:
                        self.requires_category[category] = requires

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

    def addEdge(self, node):
        self.edges.append(node)

    def mangleName(self):
        return self.name.replace("-","_")

    def printNode(self):
        print(self.name)

    def printDotHeader(self):
        txt = "digraph G {\n"
        txt += '  size = "11,17";\n'
        txt += '  ranksep = "1";\n'
        txt += '  rankdir=TB;\n'
        txt += self.printDotTitle()
        txt += self.staticFormat()
        return txt

    def staticFormat(self):
        # this is a result of palying with dot figure and aligning admixes
        # so that they produce fewer adges and less white space.
        # create an invisible top-bottom ancoring nodes for fixing
        # admixes position at specific rank
        txt = '{ node [shape=plaintext, style=invis];\n'
        txt += '  11 -> 12 -> 13 -> 14 [style=invis]; };\n'
        txt += '{rank = same; 11; cuda_admix; perl_admix; fileformats_admix; genomics_admix; biotools_admix; chemistry_admix; pytorch_admix};\n'
        txt += '{rank = same; 12; mathlibs_admix; buildlibs_admix; python_admix; foundation_admix; gcc_admix};\n'
        txt += '{rank = same; 13; rust_admix; simulations_admix; R4_admix; imaging_admix; buildtools_admix };\n'
        txt += '{rank = same; 14; tensorflow_admix; systools_admix; yaml2rpm; conda_admix; bioconda_admix; nfsapps_admix; julia_admix};\n'
        return txt

    def printDotTitle(self):
        title = "Software Modules and Dependencies (%s)\n\nReusable  packages  created  with  yaml2rpm\nhttps://github.com/RCIC-UCI-Public/yaml2rpm" % self.created
        txt = '  labelloc="t";\n  fontsize="24.0";\n'
        txt += '  fontcolor=%s;\n' % self.colorTitle
        txt += '  fontname="Times-Roman-Bold";\n'
        txt += '  fontsize=24;\n'
        txt += '  label="%s";\n' % title
        return txt

    def printDotTrailer(self):
        return "}\n"

    def printDotNotation(self):
        txt = "\n## %s\n" % self.name
        txt += '%s [shape=plaintext, %s\n' % (self.mangleName(),self.labelheader)

        reqlist='<TR><TD bgcolor="%s"><font color="%s">requires:</font>\n  <BR/>' % (self.colorRequiresBG,self.colorSpecs)
        if self.requires is not None:
           reqlist="%s%s" % (reqlist, "\n  <BR/>".join(self.requires))
        reqlist = reqlist + "\n</TD></TR>\n"

        provlist='<TR><TD bgcolor="%s"><font color="%s">provides:</font>\n  <BR/>' % (self.colorProvidesBG,self.colorSpecs)
        if self.provides is not None:
           provlist="%s%s" % (provlist, "\n  <BR/>".join(self.provides))
        provlist = provlist + "\n</TD></TR>\n"

        txt += '%s%s%s%s]' % (self.namepattern % (self.colorLabelBG,self.name), reqlist, provlist,self.labeltrailer)

        edgenames = map(lambda x: x.mangleName(), self.edges)
        for edge in edgenames:
            txt += "\n%s -> %s;" % (self.mangleName(), edge)
        txt += "\n"
        return txt

#####################################################
class Content:
    def __init__(self, args=None):
        self.prog = args[0]
        self.args = args[1:]     # command line arguments
        self.depgraph = "dot-byadmix"
        self.catgraph = "dot-bycategory"
        self.ordergraph = "dot-buildorder"

        self.parseArg()

    def parseArg(self):
        if not self.args:
            self.infile = "depinfo.yaml"
            return

        if self.args[0] in ["-h","--h","help","-help","--help"]:
            helpStr = "Usage: %s [inFile]\n" % self.prog
            helpStr += "      If inpile is not provideed a default is depinfo.yaml\n"
            print (helpStr)
            sys.exit(0)

        if len(self.args) == 1:
            self.infile = self.args[0]
        return

    def readYaml(self):
        f = open(self.infile)
        admixes = yaml.load(f)
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

    def Debug(self):
        for node in self.nodes:
            print ("XXX",node.name)
            print ("XXX    self.requires ", len(node.requires),  node.requires)
            print ("XXX    requires_category ", node.requires_category)
            print ("XXX    self.provides ",  len(node.provides), node.provides)
            print ("XXX    provides_category ", node.provides_category)

    def createDepProviders(self):
        providers = []
        for node in self.nodes:
           p = node.getProvides()
           name = node.getNodeName()
           if p is not None:
               providers.extend([(mod, name) for mod in p])

        # Create a dictionary the maps provides to admix names.
        self.provlist = { x[0]:x[1] for x in providers }

    def connectDepGraph(self):
        for node in self.nodes:
            reqs = node.getRequires()
            ## this converts the requires (a module name ) to the admix name that provides the module.
            ## don't fail if there is no admix the provides the module (might be system provided)
            reqsByAdmix = []
            if reqs is not None:
                for r in reqs:
                    try:
                        providerAdmix = self.provlist[r]
                        if providerAdmix not in reqsByAdmix:
                            reqsByAdmix.extend([providerAdmix])
                    except:
                        pass
            ## remove self-dependency
            edges = list(filter(lambda x: x != node.name, reqsByAdmix))
            for edge in edges:
                edgeNode = list(filter(lambda x: x.name == edge, self.nodes))[0]
                node.addEdge(edgeNode)

    def showDepGraph(self):
        lines = self.nodes[0].printDotHeader()
        for admix in self.nodes:
            lines += admix.printDotNotation()
        lines += self.nodes[0].printDotTrailer()

        f = open(self.depgraph, "w")
        f.writelines(lines)
        f.close()

    def buildOrderGraph(self):
        # create build order graph
        txt = "digraph G {\n"
        txt += '  size = "11,17";\n'
        txt += '  ranksep = "2";\n'
        txt += '  rankdir=TB;\n'
        txt += '  labelloc="t";\n'
        txt += '  fontcolor=dodgerblue4;\n'
        txt += '  fontname="Times-Roman-Bold";\n'
        txt += '  fontsize=24;\n'
        txt += '  label="Admix build order\n\n";\n'

        # static content. just slightly different then without ranking
        # this gives a better visibility
        txt += "{ node [shape=plaintext, color=blue fontsize=24];\n"
        txt += "  1 -> 2 -> 3 -> 4 -> 5 -> 6 -> 7 -> 8 -> 9  [style=invis]; };\n"
        txt += "{rank = same; 1; yaml2rpm;};\n"
        txt += "{rank = same; 2; gcc_admix; buildtools_admix};\n"
        txt += "{rank = same; 3; systools_admix; foundation_admix; };\n"
        txt += "{rank = same; 4; buildlibs_admix; mathlibs_admix} ;\n"
        txt += "{rank = same; 5; R4_admix;rust_admix simulations_admix; fileformats_admix; };\n"
        txt += "{rank = same; 6; python_admix;cuda_admix; perl_admix};\n"
        txt += "{rank = same; 7; imaging_admix;  tensorflow_admix; biotools_admix;chemistry_admix;pytorch_admix};\n"
        txt += "{rank = same; 8; genomics_admix};\n"
        txt += "{rank = same; 9; conda_admix; bioconda_admix; nfsapps_admix; julia_admix};\n"

        for admix in self.nodes:
            txt += "\n## %s\n" % admix.name
            txt += '%s [shape=plaintext, %s\n' % (admix.mangleName(),admix.labelheader)
            txt += '%s%s]' % (admix.namepattern % (admix.colorLabelBG,admix.name), admix.labeltrailer)

            edgenames = map(lambda x: x.mangleName(), admix.edges)
            for edge in edgenames:
                txt += "\n%s -> %s;" % (admix.mangleName(), edge)
            txt += "\n"

        txt += admix.printDotTrailer()

        f = open(self.ordergraph, "w")
        f.writelines(txt)
        f.close()

    def buildDepGraph(self):
        # create admix dependency graph
        self.createDepProviders()
        self.connectDepGraph()
        self.showDepGraph()

    def createCategoryNodes(self):
        # creat category dependency graph
        categories = []
        for node in self.nodes:
            categories += node.provides_category.keys()
        categories = list(OrderedDict.fromkeys(categories))
        self.categories = [Category(name,self.created) for name in categories]

    def createCategoryEdges(self):
        # add required and provided modules to categorries
        for category in self.categories:
            name = category.name
            for node in self.nodes:
                # add provided modules by category
                for provCatName,provCatModules in node.provides_category.items():
                    if provCatName == name:
                        category.addCategoryProvides(provCatModules)
                # add required modules by category
                for reqCatName,reqCatModules in node.requires_category.items():
                    if reqCatName == name:
                        category.addCategoryRequires(reqCatModules)

            category.orderCategoryModules()

        # dictionary of all modules, key is module name value is its category
        allm = {}
        for category in self.categories:
            catname = category.name
            provides = category.getCategoryProvides()
            for p in provides:
                allm[p] = catname

        # create adges from requires and change the mod name to its category
        for category in self.categories:
            category.addCategoryEdges(allm)

    def showCategoryGraph(self):
        head = self.categories[0]
        lines = head.printCategoryDotHeader()

        for category in self.categories:
            lines += category.printCategoryDotNotation()
        lines += head.printCategoryDotTrailer()

        f = open(self.catgraph, "w")
        f.writelines(lines)
        f.close()

    def buildCategoryGraph(self):
        self.createCategoryNodes()
        self.createCategoryEdges()
        if self.categories:
            self.showCategoryGraph()

    def run(self):
        self.readYaml()
        self.processYamlInfo()
        self.buildDepGraph()
        self.buildOrderGraph()
        self.buildCategoryGraph()

#####################################################
if __name__ == "__main__":
    app = Content(sys.argv)
    app.run()
