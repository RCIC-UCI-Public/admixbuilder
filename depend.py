#!/usr/bin/env python
from __future__ import print_function
import re
import sys
import subprocess
import yaml
from datetime import date

class Node(object):
    def __init__(self,name,admixes,created):
        self.name = name
        self.edges = []
        self.requires = []
        self.provides = []
        self.created = created;
        if name in admixes.keys(): 
           self.requires = admixes[name]['requires']
           self.provides = admixes[name]['provides']
        self.labelheader = 'label=<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0">'
        self.labeltrailer = "</TABLE>>"
        self.namepattern = '<TR><TD bgcolor="lightblue"><font point-size="16" face="Times-Bold">%s</font></TD></TR>\n'

    def addEdge(self, node):
        self.edges.append(node)

    def mangleName(self):
        return self.name.replace("-","_")

    def resolve(self,resolved):
        for edge in self.edges:
            if edge not in resolved:
                edge.resolve(resolved)
        resolved.append(self)

    def printNode(self):
        print(self.name)

    def printDotHeader(self):
        print("digraph G {")
        print('  size = "11,17";')
        print('  ranksep = "1";')
        print('  rankdir=TB;')
        self.printTitle()
        self.staticFormat()

    def staticFormat(self):
        # this is a result of palying with dot figure and aligning admixes
        # so that they produce fewer adges and less white space.
        # create an invisible top-bottom ancoring nodes for fixing
        # admixes position at specific rank
        print('{ node [shape=plaintext, style=invis];')
        print('  11 -> 12 -> 13 -> 14 [style=invis]; };')
        print('{rank = same; 11; cuda_admix; perl_admix; fileformats_admix; genomics_admix; biotools_admix; chemistry_admix; pytorch_admix};')
        print('{rank = same; 12; mathlibs_admix; buildlibs_admix; python_admix; foundation_admix; gcc_admix};')
        print('{rank = same; 13; rust_admix; simulations_admix; R4_admix; imaging_admix; buildtools_admix };')
        print('{rank = same; 14; tensorflow_admix; systools_admix; yaml2rpm; conda_admix; bioconda_admix; nfsapps_admix; julia_admix};')

    def printTitle(self):
        title = "Software Modules and Dependencies (%s)\n\nReusable  packages  created  with  yaml2rpm\nhttps://github.com/RCIC-UCI-Public/yaml2rpm" % self.created
        print('  labelloc="t";\n  fontsize="24.0";')
        print('  fontcolor=dodgerblue4;')
        print('  fontname="Times-Roman-Bold";')
        print('  fontsize=24;')
        print('  label="%s";' % title)

    def printDotTrailer(self):
        print("}")

    def printDotNotation(self):
        print("\n## %s" % self.name)
        reqlist='<TR><TD bgcolor="mintcream"><font color="blue">requires:</font>\n  <BR/>'
        provlist='<TR><TD bgcolor="ghostwhite"><font color="blue">provides:</font>\n  <BR/>'
        # print ("xxx %s xxx" % self.name)
        if self.requires is not None:
           reqlist="%s%s" % (reqlist, "\n  <BR/>".join(self.requires))
        if self.provides is not None:
           provlist="%s%s" % (provlist, "\n  <BR/>".join(self.provides))
        reqlist = reqlist + "\n</TD></TR>\n"
        provlist = provlist + "\n</TD></TR>\n"
        print ('%s [shape=plaintext, %s' % (self.mangleName(),self.labelheader))
        print ('%s%s%s%s]' % (self.namepattern % self.name, reqlist, provlist,self.labeltrailer))
        edgenames = map(lambda x: x.mangleName(), self.edges)
        for edge in edgenames:
            print ("%s -> %s;" % (self.mangleName(), edge))


# Create Graph nodes for every module
f=open("deplist.yaml")
admixes = yaml.load(f)
try:
   created = admixes['created']
   del admixes['created']
except:
   created = str(date.today())

nodes = [ Node(name,admixes,created) for name in admixes.keys()]

providers = [] 
for am in admixes.keys():
   p = admixes[am]['provides']
   if p is not None:
       providers.extend([(mod, am) for mod in p])

# Create a dictionary the maps provides to admix names.
provlist = { x[0]:x[1] for x in providers }

# make a  master Node to and add all edges to it to make sure that the dependency graph is connected
master = Node('ROOT',admixes,created)
for node in nodes:
    master.addEdge(node)
    reqs = admixes[node.name]['requires']
    ## this converts the requires (which is a module) the admix that provides the module.
    ## don't fail if there is no admix the provides the module (might be system provided)
    reqsByAdmix = []
    if reqs is not None:
        for r in reqs:
            try:
                providerAdmix = provlist[r]
                if providerAdmix not in reqsByAdmix:
                    reqsByAdmix.extend([providerAdmix])
            except:
                pass
    ## remove self-dependency
    edges = list(filter(lambda x: x != node.name, reqsByAdmix)) 
    for edge in edges:
        edgeNode = list(filter(lambda x: x.name == edge, nodes))[0]
        node.addEdge(edgeNode)
    # node.printNode()
resolved = []

# Resolve 
master.resolve(resolved)
master.printDotHeader()
for admix in resolved:
    # print("%s" % admix.name)
    if admix.name != "ROOT":
       admix.printDotNotation()
master.printDotTrailer()
