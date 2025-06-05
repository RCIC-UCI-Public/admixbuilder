#!/usr/bin/env python
#from __future__ import print_function
import re
import sys
import os
import ruamel.yaml
import argparse
from datetime import datetime
from dateutil.parser import parse
from collections import OrderedDict

class Package(object):
    def __init__(self, line):
        self.start = None    # datetime object for start building time
        self.end = None      # datetime object for end building time
        self.minutes = None  # minutes took to build RPM package
        self.pkgname = line.split()[-1]  # package name, for example x-module.pkg

    def addTime(self, date_str, flag):
        dt_object = parse(date_str)
        if flag == 0:
            self.start = dt_object
        else:
            self.end = dt_object

    def printPackage(self):
        print("%s = %s " % (self.pkgname, self.minutes))

    def findMinutes(self):
        # calculate the difference (seconds) between the datetime objects
        # and convert to minutes
        try:
            delta = self.end - self.start
            self.minutes = delta.total_seconds() / 60
        except:
            self.minutes = None

    def getMinutes(self):
        return self.minutes

class App:
    def __init__(self, args=None):
        self.prog = args[0]
        self.args = args[1:]     # command line arguments
        self.strStart = "===== Building "
        self.strEnd = "===== Completed "
        self.packages = {}       # key is a uniq string identifier, value is a Package object
        self.fig = "histogram"

        self.parseArg()

    def parseArg(self):
        # process command line arguments 
        description = "Parse log files info and get time in minutes how long packages were built"
        helpinfile = "file name to parse.\n"
        parser = argparse.ArgumentParser(description=description, formatter_class=argparse.RawTextHelpFormatter)
        # required positional argument
        parser.add_argument("infile",  action="store", help=helpinfile)

        args = parser.parse_args()
        if not os.path.isfile(args.infile):
            sys.stderr.write("Input file %s does not exist\n" % args.infile)
            sys.exit(-1)

        self.infile = args.infile
        return

    def readInput(self):
        # read input log file (already only with needed lines in any order)
        self.lines = []
        f = open(self.infile)
        for i, line in enumerate(f):
            self.lines.append (line)
        f.close()
        return

    def processTimes(self, line, flag):
        # create a Package object if new  and add it to a dictionary
        # or add a datetime to the object if the object already exist
        index1 = line.find("(")
        index2 = line.find(")")
        logprefix = line[:index1]         # uniq identifier, dict key
        date_str = line[index1+1:index2]  # time string to convert to datetime object
        if logprefix in self.packages:
            self.packages[logprefix].addTime(date_str, flag)
        else:
            self.packages[logprefix] = Package(logprefix)
            self.packages[logprefix].addTime(date_str, flag)

    def parseLines(self):
        list_building = []
        list_completed = []
        strStartLen = len(self.strStart)
        strEndLen = len(self.strEnd)
        for line in self.lines:
            index1 = line.find(self.strStart)
            if index1 > 0 :
                newline = line[:index1] + line[index1+strStartLen:]
                list_building.append(newline)
            else:
                index2 = line.find(self.strEnd)
                if index2 > 0 :
                    newline = line[:index2] + line[index2+strEndLen:]
                    list_completed.append(newline)

        # add Package object
        for i in list_building:
            self.processTimes(i, 0)
        # update Package object
        for i in list_completed:
            self.processTimes(i, 1)

        #print ("DEBUG building")
        #for i in list_building: print (i)
        #print ("DEBUG completed")
        #for i in list_completed: print (i)

        self.minutes = []
        for k,v in self.packages.items():
            v.findMinutes()
            minutes = v.getMinutes()
            if minutes: 
                self.minutes.append(minutes)
            #print (k, v.getMinutes())

    def plotTimeHist(self):
        import matplotlib.pyplot as plt
        import numpy as np
        data = self.minutes

        data1 = [x for x in data if x > 1]
        data2 = [x for x in data if x <= 1]
        bins1 = int(max(data1)/10)
        bins2 = 20

        fig, axes = plt.subplots(nrows=1, ncols=2, figsize=(10, 5))

        # Plot histograms
        axes[0].hist(data1, bins=bins1, color='darkviolet', edgecolor='black')
        axes[0].set_title('Histogram of build times > 1min')
        axes[0].set_xlabel('Build time values (min)')
        axes[0].set_ylabel('Frequency')

        axes[1].hist(data2, bins=bins2, color='deepskyblue', edgecolor='black')
        axes[1].set_title('Histogram of build times <= 1min')
        axes[1].set_xlabel('Build time values (min)')
        axes[1].set_ylabel('Frequency')

        plt.tight_layout() # adjust layout
        plt.savefig("%s.png" % self.fig) # save the plot
        plt.close(1)
 

        # single plot is not good  as there is a lot skewing for small packages 
        # Sample data
        #dataN = [x for x in data if x > 1]
        #bins = int(max(dataN)/10)

        # Plot histogram
        #plt.hist(dataN, bins=bins, color='darkviolet', edgecolor='black')
        #plt.title('Histogram of packages build times')
        #plt.xlabel('Build time values')
        #plt.ylabel('Frequency')
        #plt.savefig("%s.png" % self.fig)
        #plt.close(1)
       
    def run(self):
        self.readInput()
        self.parseLines()
        self.plotTimeHist()

#####################################################
if __name__ == "__main__":
    app = App(sys.argv)
    app.run()
