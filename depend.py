#!/usr/bin/env python
from __future__ import print_function
import re
import sys
import subprocess
import yaml

class Node(object):
    def __init__(self,name,admixes):
        self.name = name
        self.edges = []
        self.requires = []
        self.provides = []
        if name in admixes.keys(): 
           self.requires = admixes[name]['requires']
           self.provides = admixes[name]['provides']
        self.labelheader = 'label=<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0">'
        self.labeltrailer = "</TABLE>>"
        self.namepattern = '<TR><TD BGCOLOR="lightblue">%s</TD></TR>\n'


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

    def printDotTrailer(self):
        print("}")

    def printDotNotation(self):
        reqlist="<TR><TD> requires:\n  <BR/>"
        provlist="<TR><TD> provides:\n  <BR/>"
        # print ("xxx %s xxx" % self.name)
        if self.requires is not None:
           reqlist="%s%s" % (reqlist, "\n  <BR/>".join(self.requires))
        if self.provides is not None:
           provlist="%s%s" % (provlist, "\n  <BR/>".join(self.provides))
        reqlist = reqlist + "\n</TD></TR>"       
        provlist = provlist + "\n</TD></TR>"       
        print ('%s [shape=plaintext, %s' % (self.mangleName(),self.labelheader))
        print ('%s%s%s%s]' % (self.namepattern % self.name, reqlist, provlist,self.labeltrailer))
	edgenames = map(lambda x: x.mangleName(), self.edges)
        for edge in edgenames:
            print ("%s -> %s;" % (self.mangleName(), edge))


# Create Graph nodes for every module
f=open("deplist.yaml")
admixes = yaml.load(f)
nodes = [ Node(name,admixes) for name in admixes.keys()]

providers = [] 
for am in admixes.keys():
   p = admixes[am]['provides']
   if p is not None:
	providers.extend([(mod, am) for mod in p])

# Create a dictionary the maps provides to admix names.
provlist = { x[0]:x[1] for x in providers }

# make a  master Node to and add all edges to it to make sure that the dependency graph is connected
master = Node('ROOT',admixes)
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
    edges = filter(lambda x: x != node.name, reqsByAdmix) 

    for edge in edges:
	edgeNode = filter(lambda x: x.name == edge, nodes)[0]
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
