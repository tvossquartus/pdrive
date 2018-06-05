
from os import walk
from os import stat
#from os import path
import os
import datetime
import csv
#import time


# code to find owner from:
# https://stackoverflow.com/questions/8086412/howto-determine-file-owner-on-windows-using-python-without-pywin32

import ctypes as ctypes
from ctypes import wintypes as wintypes

kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
advapi32 = ctypes.WinDLL('advapi32', use_last_error=True)

ERROR_INVALID_FUNCTION  = 0x0001
ERROR_FILE_NOT_FOUND    = 0x0002
ERROR_PATH_NOT_FOUND    = 0x0003
ERROR_ACCESS_DENIED     = 0x0005
ERROR_SHARING_VIOLATION = 0x0020

SE_FILE_OBJECT = 1
OWNER_SECURITY_INFORMATION = 0x00000001
GROUP_SECURITY_INFORMATION = 0x00000002
DACL_SECURITY_INFORMATION  = 0x00000004
SACL_SECURITY_INFORMATION  = 0x00000008
LABEL_SECURITY_INFORMATION = 0x00000010

_DEFAULT_SECURITY_INFORMATION = (OWNER_SECURITY_INFORMATION |
    GROUP_SECURITY_INFORMATION | DACL_SECURITY_INFORMATION |
    LABEL_SECURITY_INFORMATION)

LPDWORD = ctypes.POINTER(wintypes.DWORD)
SE_OBJECT_TYPE = wintypes.DWORD
SECURITY_INFORMATION = wintypes.DWORD

class SID_NAME_USE(wintypes.DWORD):
    _sid_types = dict(enumerate('''
        User Group Domain Alias WellKnownGroup DeletedAccount
        Invalid Unknown Computer Label'''.split(), 1))

    def __init__(self, value=None):
        if value is not None:
            if value not in self.sid_types:
                raise ValueError('invalid SID type')
            wintypes.DWORD.__init__(value)

    def __str__(self):
        if self.value not in self._sid_types:
            raise ValueError('invalid SID type')
        return self._sid_types[self.value]

    def __repr__(self):
        return 'SID_NAME_USE(%s)' % self.value

PSID_NAME_USE = ctypes.POINTER(SID_NAME_USE)

class PLOCAL(wintypes.LPVOID):
    _needs_free = False
    def __init__(self, value=None, needs_free=False):
        super(PLOCAL, self).__init__(value)
        self._needs_free = needs_free

    def __del__(self):
        if self and self._needs_free:
            kernel32.LocalFree(self)
            self._needs_free = False
PACL = PLOCAL
class PSID(PLOCAL):
    def __init__(self, value=None, needs_free=False):
        super(PSID, self).__init__(value, needs_free)

    def __str__(self):
        if not self:
            raise ValueError('NULL pointer access')
        sid = wintypes.LPWSTR()
        advapi32.ConvertSidToStringSidW(self, ctypes.byref(sid))
        try:
            return sid.value
        finally:
            if sid:
                kernel32.LocalFree(sid)
class PSECURITY_DESCRIPTOR(PLOCAL):
    def __init__(self, value=None, needs_free=False):
        super(PSECURITY_DESCRIPTOR, self).__init__(value, needs_free)
        self.pOwner = PSID()
        self.pGroup = PSID()
        self.pDacl = PACL()
        self.pSacl = PACL()
        # back references to keep this object alive
        self.pOwner._SD = self
        self.pGroup._SD = self
        self.pDacl._SD = self
        self.pSacl._SD = self

    def get_owner(self, system_name=None):
        if not self or not self.pOwner:
            raise ValueError('NULL pointer access')
        return look_up_account_sid(self.pOwner, system_name)

    def get_group(self, system_name=None):
        if not self or not self.pGroup:
            raise ValueError('NULL pointer access')
        return look_up_account_sid(self.pGroup, system_name)
def _check_bool(result, func, args):
    if not result:
        raise ctypes.WinError(ctypes.get_last_error())
    return args

# msdn.microsoft.com/en-us/library/aa376399
advapi32.ConvertSidToStringSidW.errcheck = _check_bool
advapi32.ConvertSidToStringSidW.argtypes = (
    PSID, # _In_   Sid
    ctypes.POINTER(wintypes.LPWSTR)) # _Out_ StringSid

# msdn.microsoft.com/en-us/library/aa379166
advapi32.LookupAccountSidW.errcheck = _check_bool
advapi32.LookupAccountSidW.argtypes = (
    wintypes.LPCWSTR, # _In_opt_  lpSystemName
    PSID,             # _In_      lpSid
    wintypes.LPCWSTR, # _Out_opt_ lpName
    LPDWORD,          # _Inout_   cchName
    wintypes.LPCWSTR, # _Out_opt_ lpReferencedDomainName
    LPDWORD,          # _Inout_   cchReferencedDomainName
    PSID_NAME_USE)    # _Out_     peUse

# msdn.microsoft.com/en-us/library/aa446645
advapi32.GetNamedSecurityInfoW.restype = wintypes.DWORD
advapi32.GetNamedSecurityInfoW.argtypes = (
    wintypes.LPWSTR,       # _In_      pObjectName
    SE_OBJECT_TYPE,        # _In_      ObjectType
    SECURITY_INFORMATION,  # _In_      SecurityInfo
    ctypes.POINTER(PSID),  # _Out_opt_ ppsidOwner
    ctypes.POINTER(PSID),  # _Out_opt_ ppsidGroup
    ctypes.POINTER(PACL),  # _Out_opt_ ppDacl
    ctypes.POINTER(PACL),  # _Out_opt_ ppSacl
    ctypes.POINTER(PSECURITY_DESCRIPTOR)) # _Out_opt_ ppSecurityDescriptor
def look_up_account_sid(sid, system_name=None):
    SIZE = 256
    name = ctypes.create_unicode_buffer(SIZE)
    domain = ctypes.create_unicode_buffer(SIZE)
    cch_name = wintypes.DWORD(SIZE)
    cch_domain = wintypes.DWORD(SIZE)
    sid_type = SID_NAME_USE()
    advapi32.LookupAccountSidW(system_name, sid, name, ctypes.byref(cch_name),
        domain, ctypes.byref(cch_domain), ctypes.byref(sid_type))
    return name.value, domain.value, sid_type
def get_file_security(filename, request=_DEFAULT_SECURITY_INFORMATION):
    # N.B. This query may fail with ERROR_INVALID_FUNCTION
    # for some filesystems.
    pSD = PSECURITY_DESCRIPTOR(needs_free=True)
    error = advapi32.GetNamedSecurityInfoW(filename, SE_FILE_OBJECT, request,
                ctypes.byref(pSD.pOwner), ctypes.byref(pSD.pGroup),
                ctypes.byref(pSD.pDacl), ctypes.byref(pSD.pSacl),
                ctypes.byref(pSD))
    if error != 0:
        raise ctypes.WinError(error)
    return pSD

# to do list, in no particular order:
#
# 1. auto email a list of flagged files to each person
# 2. create graphics from data
# 3. write csv of all data
# 4. add filename (slkfjs.ext) to class.. (also gather to list and output)
# 5. add extension (.ext) to class.. (also gather to list and output)
# 6. move write csv into a function that takes any number of user objects 
# 7. gather information about how long each part of this code takes to run
# 8. write a gui where the user can input (path to search, GO, sizelimit)
# 8a. eventually we can add select file type to look for
# 9. understand and condense getting the user id ^^ above
# 10. can we move function into a different script??


def shouldflag(filename, datemodified):
    filename, extension = os.path.splitext(filename)

    # check to see if this file extension is expected to be deletable
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
def getowner(thisfile):
    pSD = get_file_security(thisfile)
    owner, owner_domain, owner_sid_type = pSD.get_owner()
    return owner
def writecsv(users):
    # task 6
    x=1

class userstat():
    def __init__(self):
        self.file = []
        self.size = []
        self.created = []
        self.modified = []
        self.flagged = []
        self.id = ""
    def setid(self,id):
        self.id = id
    def addfile(self,file):
        self.file.append(file)
    def addsize(self,size):
        self.size.append(size)
    def addcreated(self,created):
        self.created.append(created)
    def addmodified(self,modified):
        self.modified.append(modified)
    def addflag(self,flag):
        self.flagged.append(flag)
    
# recursive function to search through each file
def nextdir (thispath):
    # initialize a list which contains an object for each user who has ever created a file
    allusers = []
    numusers = 0
    # walk through each folder
    for (dirpath, dirnames, filenames) in walk(thispath):    
        # walk through each file
        for filename in filenames:
            thisfile = dirpath + '\\' + filename
            # when the path is longer than 260 characters then microsoft cannot get statistics about this file.. filenotfound error
            if len(thisfile)>=260:
                continue
            # get statictics about this file
            statinfo = stat(thisfile)
            # file size in bytes (not size on disk) in Gb
            # TODO: get file size on disk
            size = statinfo.st_size/1E9
            # only log the file if it is larger than the limit
            if size > sizelimit: 
                # find this users object in the list
                userid = 0
                owner = getowner(thisfile)
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
                allusers[userid].addfile(thisfile) # add file to this user's list
                allusers[userid].addsize(size) # add size to this user's list
                datemodified = datetime.datetime.fromtimestamp(statinfo.st_mtime).strftime("%Y%m%d")
                allusers[userid].addmodified(datemodified) # add date modified to this user's list
                allusers[userid].addcreated(datetime.datetime.fromtimestamp(statinfo.st_ctime).strftime("%Y%m%d")) # add date created to this user's list
                # check if this file is flaged to be deleted
                if shouldflag(filename, datemodified) == True:
                    # if so add this index to a list
                    allusers[userid].addflag(len(allusers[userid].file))
    return allusers
                
# only add files to the list if they are greater than this limit (Gb)
sizelimit = 0.2                    
                
mypath = "P:/1377_OSC_ONSITE"
mypath = "P:/3379-Scaled-Stratolaunch"
#mypath = "P:/4041_PANASONIC_BOMBARDIER_BIRDSTRIKE"

allusers = nextdir(mypath)

for usernum in range(len(allusers)):
    with open('data_%s.csv' %(allusers[usernum].id),'w') as outputfile:
        for filenum in range(len(allusers[usernum].file)):
            var1 = allusers[usernum].id
            var2 = allusers[usernum].size[filenum]
            var3 = allusers[usernum].created[filenum]
            var4 = allusers[usernum].modified[filenum]
            var5 = "False"
            var6 = allusers[usernum].file[filenum]
            # check if this particular item is flagged
            for flagid in range(len(allusers[usernum].flagged)):
                if allusers[usernum].flagged[flagid] > filenum:
                    break
                elif allusers[usernum].flagged[flagid] == filenum:
                    var5 = "True"
                    break
            outputfile.write('%s,%.2f,%s,%s,%s,%s\r' % (var1,var2,var3,var4,var5,var6))





