
from os import walk 
from os import stat
import os
import datetime
from getuserinfo import *

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
# -. how do we loop through a class' object (used to determine length of each list) https://stackoverflow.com/questions/19151/build-a-basic-python-iterator
# BUG. handle file path lengths that are longer than 260 characters (microsoft limitation)
# -. update import statements to be more concise
# -. clean up recurssive code.. can we make a function that fills an object maybe
# -. add shouldfind function which decides wether or not the file should be reported
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
        # takes in fileaddress and parses out the file extension
        self.extension.append(var)
    def addfilename(self,var):
        # takes in fileaddress and parses out the file name
        filename, extension = os.path.splitext(var)
        self.filename.append(filename)
    def addproject(self,var):
        # takes in fileaddress and parses out the project i.e. top level folder
        temp = var.split(":/")
        temp = temp[1].split("\\")
        self.project.append(temp[0])

def shouldflag(entry):

    # check to make sure this entry is only a single entry and not multiple
    #for key in entry.__dict__:
    # place holder ----
    #
    # setattr
    #

    # pulls information out of this entry object
    filename = entry.filename[-1]
    datemodified = entry.modified[-1]

    # check to see if this file extension is expected to be deletable
    _ , extension = os.path.splitext(filename)
    illegalextension = []
    illegalextension.append(".log")
    illegalextension.append(".op2")
    illegalextension.append(".Qout")
    for ext in illegalextension:
        if ext == extension:
            return True 

    # number of days since last time this file was last modified (saved)
    modifiedon = datetime.datetime.strptime(datemodified,'%Y%m%d')
    timedif = datetime.datetime.now() - modifiedon 
    days = timedif.days
    if days >= 365:
        return True
def shouldfind(fileaddress, criteria):
    #
    # add checks for other critieria to find
    # should be an or statement
    #
    if stat(fileaddress).st_size/1E9 > criteria.size[-1]:
        return True
    else:
        return False


def getowner(thisfile):
    pSD = get_file_security(thisfile)
    owner, owner_domain, owner_sid_type = pSD.get_owner()
    return owner

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

                    template = '%s,%.2f,%s,%s,%s,%s\r'

                    # FIX THIS

                    # check if this particular item is flagged
                    for flagid in range(len(allusers[usernum].flagged)):
                        if allusers[usernum].flagged[flagid] > filenum:
                            break
                        elif allusers[usernum].flagged[flagid] == filenum:
                            var5 = "True"
                            break

                    outputfile.write(template % (
                        allusers[usernum].id, 
                        allusers[usernum].size,
                        allusers[usernum].project, 
                        allusers[usernum].filename,
                        allusers[usernum].extension,
                        allusers[usernum].created, 
                        allusers[usernum].modified,
                        allusers[usernum].fileaddress
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

def addtouser(user,filename):
    #place holder
    return
    
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
            # Bug, when the path is longer than 260 characters then microsoft cannot get statistics about this file.. filenotfound error
            if len(fileaddress)>=260:
                continue
            if shouldfind(fileaddress, criteria): 
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
                allusers[userid].addsize(stat(fileaddress).st_size/1E9) 
                allusers[userid].addmodified(datetime.datetime.fromtimestamp(statinfo.st_mtime).strftime("%Y%m%d")) 
                allusers[userid].addcreated(datetime.datetime.fromtimestamp(statinfo.st_ctime).strftime("%Y%m%d"))
                allusers[userid].addproject(fileaddress)
                _, extension = os.path.splitext(fileaddress)
                allusers[userid].addextension(extension)
                allusers[userid].addfilename(filename)
                # check if this file is flaged to be deleted
                if shouldflag(allusers[userid]) == True:
                    # if so add this index to a list
                    allusers[userid].addflag(len(allusers[userid].size))

    return allusers





# only add files to the list if they are greater than this limit (Gb)
sizelimit = 0.1                    
                
#mypath = "P:/1377_OSC_ONSITE"
#mypath = "P:/3379-Scaled-Stratolaunch"
mypath = "P:/4041_PANASONIC_BOMBARDIER_BIRDSTRIKE"
#mypath = "P:/"
globpath = os.getcwd()  

criteria = userstat()
criteria.addextension(".modfem")
criteria.addsize(0.1)


allusers = nextdir(mypath)
writecsv(allusers, 2)
#concatenate(globpath,globpath+'\\fulldata.csv')





