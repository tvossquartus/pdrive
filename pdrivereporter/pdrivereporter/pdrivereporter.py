
from os import walk 
from os import stat
import os
import datetime
from getuserinfo import *

import matplotlib 


#from pandas import read_csv
#from pandas import concat
#import glob 
#import pandas


# to do list, in no particular order:
#
# Working:
# Adithya 
# -. auto email a list of flagged files to each person
# -. write csv of all data
# -. move write csv into a function that takes any number of user objects 
#
# Tim
# -. iterate through a class
# -. add criteria to shouldfind function
#
# DATA REPORTING:
# -. create graphics from data
# BUG. writing some extra comme delimited columns see Harrys output from P:/3492_PANASONIC_A320-BIRDSTRIKE\BOMBARDIER\Core Test
#
# GENERAL:
# -. gather information about how long each part of this code takes to run
# -. understand and condense getting the user id ^^ above
# -. import csv and delete items that are marked as true
# BUG. handle file path lengths that are longer than 260 characters (microsoft limitation)
# BUG. finding files without file extensions? or there are path names that are broken
# -. update import statements to be more concise
# -. clean up recurssive code.. can we make a function that fills an object maybe
# -. all functions should have input/output validation
#
# INTERFACE/USE:
# -. write a gui where the user can input (path to search, GO, sizelimit, path to save, report style)
# -----. eventually (find criteria, flag criteria)
# -. running a script/gui automatically at a certain time
#
# MOVE THINGS THAT HAVE BEEN COMPLETED HERE:
# -. can we move function into a different script??
# -----. answer: https://stackoverflow.com/questions/20309456/call-a-function-from-another-file-in-python#20309470
# -. add filename (slkfjs.ext) to class.. (also gather to list and output)
# -. add extension (.ext) to class.. (also gather to list and output)
# -. add parent directory to class.. 4438, 3379.. etc.
# -. pull extension, project,filename and add it to list.. then output
# -. shouldflag should be changed to take an individual user object
# -. add shouldfind function which decides wether or not the file should be reported
# -. how do we loop through a class' object (used to determine length of each list) https://stackoverflow.com/questions/19151/build-a-basic-python-iterator
# -------. answer getattr

class userstat():
    def __init__(self):
        self.fileaddress = [] # e.g. "c\thisfile.txt"
        self.size = []
        self.created = []
        self.modified = []
        self.flagged = []
        self.id = ""
        self.extension = [] # e.g. .log, .op2, .modfem
        self.filename = [] # e.g. thisfile
        self.project = [] # e.g. 1001_viasat, 1234_boeing
        self.keyword = []
    def setid(self,var):
        self.id = var
    def addfileaddress(self,var): 
        self.fileaddress.append(var)
    def addsize(self,var):
        self.size.append(var)
    def addcreated(self,var):
        self.created.append(var)
    def addmodified(self,var):
        self.modified.append(var)
    def addflag(self,var):
        self.flagged.append(var)
    def addextension(self,var): 
        self.extension.append(var)
    def addfilename(self,var):
        self.filename.append(var)
    def addproject(self,var):
        self.project.append(var)
    def addkeyword(self,var):
        self.keyword.append(var)

def shouldflag(entry, criteria):

    # pulls information out of this entry object
    filename = entry.filename[-1]
    datemodified = entry.modified[-1]
    extension = entry.extension[-1]

    # number of days since last time this file was last modified (saved)
    timedif = entry.modified[-1] - criteria.modified[-1]
    days = timedif.days
    if days < 0:
        return True

    for word in criteria.keyword:
        if word in entry.fileaddress[-1]:
            return True

    for ext in criteria.extension:
        if ext == extension:
            return True

    return False

    # if there is a keyword in the path/name that says delete

def shouldfind(fileaddress, criteria):
    for key in criteria.__dict__:
        if len(getattr(criteria,key)) <1:
            continue
        if key == "size":
            if getsize(fileaddress) > criteria.size[-1]:
                return True
        elif key == "extension":
            thisextension = getextension(fileaddress)
            for ext in getattr(criteria,key):
                if thisextension == ext:
                    return True
    return False
    
# -- pull data out of the file address
def getowner(thisaddress):
    pSD = get_file_security(thisaddress)
    owner, owner_domain, owner_sid_type = pSD.get_owner()
    return owner
def getextension(thisaddress):
    _ , extension = os.path.splitext(thisaddress)
    return extension
def getdatemodified(thisaddress):
    return datetime.datetime.fromtimestamp(stat(thisaddress).st_mtime)
def getdatecreated(thisaddress):
    return datetime.datetime.fromtimestamp(stat(thisaddress).st_ctime)
def getproject(thisaddress):
    temp = thisaddress.split("\\")
    return temp[1]
def getsize(thisaddress):
    return stat(thisaddress).st_size/1073741824

# users, savepath, option
def writecsv(allusers, option):

    # option 1... all data in one file
    if option == 1:
        x=1
    # option 2... each users data in a unique file
    elif option == 2:
        for usernum in range(len(allusers)):
            with open('data_%s.csv' %(allusers[usernum].id),'w') as outputfile:
                for filenum in range(len(allusers[usernum].size)):

                    template = '%s,%.2f,%s,%s,%s,%s,%s,%s,%s\r'
                    datetemplate = "%Y%m%d"
                    isflagged = "False"

                    # check if this particular item is flagged
                    for flagid in range(len(allusers[usernum].flagged)):
                        if allusers[usernum].flagged[flagid] > filenum:
                            break
                        elif allusers[usernum].flagged[flagid] == filenum:
                            isflagged = "True"
                            break

                    outputfile.write(template % (
                        allusers[usernum].id, 
                        allusers[usernum].size[filenum],
                        allusers[usernum].project[filenum], 
                        allusers[usernum].filename[filenum],
                        allusers[usernum].extension[filenum],
                        allusers[usernum].created[filenum].strftime(datetemplate), 
                        allusers[usernum].modified[filenum].strftime(datetemplate),
                        isflagged,
                        allusers[usernum].fileaddress[filenum]
                        ))
    return 

# Creates one data file. Don't have to use if we have a better way
def concatenate(inputdir, outputdir):
    os.chdir(inputdir)
    filelist = glob.glob("*data_") # Grab all csv files
    fulldata = []
    for filename in filelist:
        print(filename)
        datainfile = pandas.read_csv(filename,header = None)
        fulldata.append(datainfile)
    concatdata = pandas.concat(fulldata,axis=0)
    concatdata.to_csv(outputdir,index=None)
   
# recursive function to search through each file
def nextdir (thispath):
    # initialize a list which contains an object for each user who has ever created a file
    allusers = []
    numusers = 0
    # walk through each folder
    for (dirpath, dirnames, filenames) in walk(thispath):    
        print(dirpath)
        # walk through each file
        for filename in filenames:
            fileaddress = dirpath + '\\' + filename
            fileaddress = os.path.abspath(fileaddress)
            # Bug, when the path is longer than 260 characters then microsoft cannot get statistics about this file.. filenotfound error
            if len(fileaddress)>=260:
                continue
            if shouldfind(fileaddress, lookcriteria): 
                # find this users object in the list
                userid = 0
                owner = getowner(fileaddress)
                for user in allusers:
                    if user.id==owner:
                        break
                    else: 
                        userid = userid + 1
                # if the user does not have an object in the list.. then make one
                if len(allusers) == userid:
                    numusers = numusers + 1
                    allusers.append(userstat()) # add a new user object to list
                    allusers[userid].setid(owner) # assign user id to this object

                # add information to the users object
                allusers[userid].addfileaddress(fileaddress) 
                allusers[userid].addsize(getsize(fileaddress)) 
                allusers[userid].addmodified(getdatemodified(fileaddress)) 
                allusers[userid].addcreated(getdatecreated(fileaddress))
                allusers[userid].addproject(getproject(fileaddress))
                allusers[userid].addextension(getextension(fileaddress))
                allusers[userid].addfilename(filename)
                # check if this file is flaged to be deleted
                if shouldflag(allusers[userid], flagcriteria) == True:
                    # if so add this index to a list
                    allusers[userid].addflag(len(allusers[userid].size))

    return allusers


              
                
#mypath = "P:/1377_OSC_ONSITE"
mypath = "P:/3379-Scaled-Stratolaunch"
#mypath = "P:/4041_PANASONIC_BOMBARDIER_BIRDSTRIKE"
#mypath = "P:/"


# if any of this criteria is satisfied then it will be documented
lookcriteria = userstat()
#for number in range(100):
#    if number < 10:
        #lookcriteria.addextension(".0%.0f" % (number))
    #elif number >= 10:
     #   lookcriteria.addextension(".%.0f" % (number))
lookcriteria.addsize(0.1)

# if any of this criteria is satisfied then it will be flagged as "deletable"
flagcriteria = userstat()
#for number in range(100):
 #   if number < 10:
  #      flagcriteria.addextension(".0%.0f" % (number))
   # elif number >= 10:
    #    flagcriteria.addextension(".%.0f" % (number))
flagcriteria.addmodified(datetime.datetime.now() - datetime.timedelta(days=2*365))
flagcriteria.addkeyword("delete")

allusers = nextdir(mypath)
writecsv(allusers, 2)

#globpath = os.getcwd()  
#concatenate(globpath,globpath+'\\fulldata.csv')





