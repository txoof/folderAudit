#!/usr/bin/env ipython
#!/usr/bin/env python
# coding: utf-8


# In[1]:


#get_ipython().magic(u'load_ext autoreload')
#get_ipython().magic(u'autoreload 2')




# In[2]:


#get_ipython().magic(u'alias nbconvert nbconvert gdrive.ipynb')




# In[ ]:


#get_ipython().magic(u'nbconvert')




# In[3]:


import logging
import oauth2client
import httplib2
import re
import time
from ssl import SSLError
from functools import wraps
from apiclient import discovery
from apiclient import errors 





# In[4]:


class GDriveError(Exception):
    pass

class NetworkError(RuntimeError):
    pass




# In[5]:


def retryer(max_retries=10, timeout=2):
    '''
    Retry on specific network related errors with timeout
    https://pragmaticcoders.com/blog/retrying-exceptions-handling-internet-connection-problems/
    '''
    logger = logging.getLogger(__name__)
    logger.debug('max_retries: {}, timeout: {}'.format(max_retries, timeout))
    def decorator(func):
        @wraps(func)
        def retry(*args, **kwargs):
            network_exceptions= (
            errors.HttpError,
            SSLError
            )
            for i in range(max_retries):
                logger.debug('attempt: {}'.format(i))
                try:
                    result = func(*args, **kwargs)
                except network_exceptions:
                    time.sleep(timeout)
                    continue
                else:
                    return result
            else:
                raise NetworkError
        return retry
    return decorator




# In[6]:


# google documentation here:
# https://developers.google.com/apis-explorer/#p/
class googledrive():
    '''
    creates a google drive interface object
    
    Accepts:
    google drive v3 service object: (discover.build('drive', 'v3', credentials = credentials_object)
    
    sets:
        userinfo (dict) - (drive.about.get) all user info
        teamdrives (list of dict) - (drive.teamdrives.list) all available team drives
    
    '''
    def __init__(self, object):
        self.logger =logging.getLogger(__name__)
        if  not isinstance(object, oauth2client.client.OAuth2Credentials):
            self.logger.critical('invalid credential object: oauth2client.client.OAtuth2Credentials expected; {} received'.format(type(object)))

            return(None)
        # create the HTTP interface (not entirely sure how this works)
        self.http = object.authorize(httplib2.Http()) 
    
        # build the api discovery service using the http
        self.service = discovery.build('drive', 'v3', http=self.http, cache_discovery=False)
        
        #self.service = object
        # https://developers.google.com/drive/v3/web/mime-types
        self.mimeTypes = {'audio': 'application/vnd.google-apps.audio',
                          'docs': 'application/vnd.google-apps.document',
                          'drawing': 'application/vnd.google-apps.drawing',
                          'file': 'application/vnd.google-apps.file',
                          'folder': 'application/vnd.google-apps.folder',
                          'forms': 'application/vnd.google-apps.form',
                          'mymaps': 'application/vnd.google-apps.map',
                          'photos': 'application/vnd.google-apps.photo',
                          'slides': 'application/vnd.google-apps.presentation',
                          'scripts': 'application/vnd.google-apps.script',
                          'sites': 'application/vnd.google-apps.sites',
                          'sheets': 'application/vnd.google-apps.spreadsheet',
                          'video': 'application/vnd.google-apps.video'}
        
        # fields to include in partial responses
        # https://developers.google.com/apis-explorer/#p/drive/v3/drive.files.create
        self.fields = ['id', 'parents', 'mimeType', 'webViewLink', 'size', 'createdTime', 'trashed', 'kind', 'name',
                      'capabilities', 'owners', 'permissions', 'files', ''] # '' is placeholder for none
    
        self.getuserinfo()
        self.listTeamDrives()

    
    @property
    def types(self):
        '''
        Display supported mimeTypes
        '''
        print('supported mime types:')
        for key in self.mimeTypes:
            #print('%10s: %s' % (key, self.mimeTypes[key]))
            print(('{:8} {val}'.format(key+':', val=self.mimeTypes[key])))
    

    def _sanitizeFields(self, fields):
        '''
        Private method for stripping whitespace and unknown field opperators
        accepts:
            fields (string)
        
        returns:
            sanitizedFields (string)'''
        fieldsProcessed=[]
        fieldsUnknown=[]
        myFields = fields.replace(' ','')
        fieldList = re.split(',\s*(?![^()]*\))', myFields)
        # remove whitespace and unknown options
        for each in fieldList:
            if any(each.startswith(i) for i in self.fields):
                fieldsProcessed.append(each)
            else:
                fieldsUnknown.append(each)
        
        return(fieldsProcessed, fieldsUnknown)

    @retryer(max_retries=5)
    def add(self, name = None, mimeType = False, parents = None, 
            fields = 'webViewLink, mimeType, id', sanitize = True):
        '''
        add a file to google drive or team drive:
        NB! when adding to the root of a team drive use the drive ID as the parent

        args:
            name (string): human readable name
            mimeType (string): mimeType (see self.mimeTypes for a complete list)
            parents (list): list of parent folders
            fields (comma separated string): properties to query and return any of the fields listed in 
                self.fields
                see https://developers.google.com/apis-explorer/#p/drive/v3/drive.files.list
            sanitize (bool): remove any field options that are not in the above list - false to allow anything
            
        '''

#         fieldsExpected = self.fields
        fieldsProcessed = []
        fieldsUnknown = []
        body={}
        
        if sanitize:
            fieldsProcessed, fieldsUnknown = self._sanitizeFields(fields)
        else:
            fieldsProcessed = fields.split(',')
            
        if len(fieldsUnknown) > 0:
            self.logger.warn('unrecognized fields: {}'.format(fieldsUnknown))
        
        
        
        if name is None:
            self.logger.error('expected a folder or file name')
            return(False)
        else:
            body['name'] = name
        
        if mimeType in self.mimeTypes:
            self.logger.debug('set mimeType: {}'.format(mimeType))
            body['mimeType'] = self.mimeTypes[mimeType]
        else:
            self.logger.warn('ignoring unknown mimeType: {}'.format(mimeType))
        
        if isinstance(parents, list):
            body['parents'] = parents
        elif parents:
            body['parents'] = [parents]
        self.logger.debug('set parent to: {}'.format(parents))
        self.logger.debug('fields: {}'.format(fieldsProcessed))
        self.logger.debug('body: {}'.format(body))
#         apiString = 'body={}, fields={}'.format(body, ','.join(fieldsProcessed))
#         self.logger.debug('api call: files().create({})'.format(apiString))
        try:
            result = self.service.files().create(supportsTeamDrives=True, body=body, fields=','.join(fieldsProcessed)).execute()
            
        except errors.HttpError as e:
            self.logger.error(e)
            raise GDriveError(e)
            return(None)        
        
        return(result)
                
    @retryer(max_retries=5)
    def search(self, name=None, trashed=False, mimeType=False, fuzzy=False, modifiedTime=None, 
               dopperator = '>', parents=None, fields=None, orderBy='createdTime', 
               teamdrive=None, sanitize=True, quiet=True ):
        '''
        search for an item by name and other properties in google drive using drive.files.list
        
        args:
            name (string): item name in google drive - required
            trashed (bool): item is not in trash - default False
            mimeType = (string): item is one of the known mime types (gdrive.mimeTypes) - default None
            fuzzy = (bool): substring search of names in drive
            date = (RFC3339 date string): modification time date string (YYYY-MM-DD)
            dopperator (date comparison opprator string): <, >, =, >=, <=  - default >
            parents = (string): google drive file id string
            orderBy = (comma separated string): order results assending by keys below - default createdTime:
                        'createdTime', 'folder', 'modifiedByMeTime', 
                        'modifiedTime', 'name', 'quotaBytesUsed', 
                        'recency', 'sharedWithMeTime', 'starred', 
                        'viewedByMeTime'
            fields (comma separated string): properties to query and return any of the files(fields) listed in 
                self.fields
                see https://developers.google.com/apis-explorer/#p/drive/v3/drive.files.list
            sanitize (bool): remove any field options that are not in the fields list - false to allow anything
            teamdrive (string): Team Drive ID string - when included only the specified Team Drive is searched
            quiet (bool): false prints all the results
                        
                        
            
        returns:
            list of file dict
        '''
        # see https://developers.google.com/drive/api/v3/search-parameters for full list
        qFeatures = ['name', 'trashed', 'mimeType', 'modifiedTime', 'parents']
        
        # formatting structure for each query feature 
        build = {'name' : 'name {} "{}"'.format(('contains' if fuzzy else '='), name),
                 'trashed' : 'trashed={}'. format(trashed),
                 'mimeType' : 'mimeType="{}"'.format(self.mimeTypes[mimeType] if mimeType in self.mimeTypes else ''),
                 'parents': '"{}" in parents'.format(parents),
                 'modifiedTime': 'modifiedTime{}"{}"'.format(dopperator, modifiedTime)}


        if sanitize and fields:
            fieldsProcessed, fieldsUnknown = self._sanitizeFields(fields)
            # only supporting the files() fields here
            fieldsProcessed = 'files({})'.format(','.join(fieldsProcessed))
        else:
            if fields:
                fieldsProcessed = fields.split(',')
            else:
                fieldsProcessed = 'files'
            fieldsUnknown = ''
            
        if len(fieldsUnknown) > 0:
            self.logger.warn('unrecognized fields: {}'.format(fieldsUnknown))
        # provides for setting trashed to True/False if the input is not None
        if not isinstance(trashed, type(None)):
            # set to true as the variable is now in use, but it's value has been set above
            trashed = True
        
        # list of query opperations
        qList = []

        # evaluate feature options; if they are != None/False, use them in building query
        for each in qFeatures:
            if eval(each):
                qList.append(build[each])
        
        apiString = 'q={}, orderBy={}, fields={})'.format(' and '.join(qList), orderBy, fieldsProcessed)
        self.logger.debug('apicall: files().list({})'.format(apiString))
        
        if not quiet:
            print(apiString)
        
        try:
            # build a query with "and" statements

            if teamdrive:
                result = self.service.files().list(q=' and '.join(qList), 
                                                   corpora='teamDrive',
                                                   includeTeamDriveItems='true',
                                                   orderBy=orderBy,                                             
                                                   teamDriveId=teamdrive, 
                                                   supportsTeamDrives='true',
                                                   fields=fieldsProcessed).execute()
            else:
                result = self.service.files().list(q=' and '.join(qList), orderBy=orderBy, fields=fieldsProcessed).execute()

        except errors.HttpError as e:
            self.logger.error(e)
            raise GDriveError(e)
            return(None)

        return(result)
    
    @retryer(max_retries=5)
    def ls(self, *args, **kwargs):
        '''
        List files in google drive using any of the following properties:
            
        accepts:
            name (string): item name in google drive - required
            trashed (bool): item is not in trash - default None (not used)
            mimeType = (string): item is one of the known mime types (gdrive.mimeTypes) - default None
            fuzzy = (bool): substring search of names in drive
            date = (RFC3339 date string): modification time date string (YYYY-MM-DD)
            dopperator (date comparison opprator string): <, >, =, >=, <=  - default >
            parent = (string): google drive file id string    
        '''
        try:
            result = self.search(*args, **kwargs)
            for eachFile in result.get('files', []):
                print(('name: {f[name]}, ID:{f[id]}, mimeType:{f[mimeType]}'.format(f=eachFile)))
            
        except GDriveError as e:
            self.logger.error(e)
            raise GDriveError(e)
            return(None)
        
        return(result)
            
    
    @retryer(max_retries=5)
    def getprops(self, fileId = None, fields = 'parents, mimeType, webViewLink', sanitize=True):
        '''
        get a file or folder's properties based on google drive fileId
        
        for a more complete list: https://developers.google.com/drive/v3/web/migration
        
        args:
            fileId (string): google drive file ID
            fields (comma separated string): properties to query and return any of the fields
                listed in self.fields
            sanitize (bool): remove any field options that are not in the above list - false to allow anything
            
        returns:
            list of dictionary - google drive file properties
            
        raises GDriveError
        '''
        fieldsExpected = self.fields
        
        fieldsProcessed = []
        fieldsUnknown = []

        # move this into a private method 
        if sanitize:
            fieldsProcessed, fieldsUnknown = self._sanitizeFields(fields)
        else:
            fieldsProcessed = fields.split(',')
        if len(fieldsUnknown) > 0:
            self.logger.error('unrecognized fields: {}'.format(fieldsUnknown))
        
        apiString = 'fileId={}, fields={}'.format(fileId, ','.join(fieldsProcessed))
        self.logger.debug('files().get({})'.format(apiString))
        try:
            result = self.service.files().get(supportsTeamDrives=True, fileId=fileId, fields=','.join(fieldsProcessed)).execute()

        except errors.HttpError as e:
            self.logger.error(e)
            raise GDriveError(e)
            return(None)
        
        return(result)
    
    @retryer(max_retries=5)
    def getpermissions(self, fileId):
        """
        get a file, folder or Team Drive's permissions
        """
        self.logger.debug('checking permissions for item id: {}'.format(fileId))
        try:
            permissions = self.service.permissions().list(fileId=fileId, 
                                                          supportsTeamDrives=True).execute()
            
        except (errors.HttpError) as e:
            if e.resp.status in [404]:
                self.logger.info('file/folder not found')
                return(None)
            else:
                self.logger.error(e)
                raise GDriveError(e)
        
        return(permissions)
    
    @retryer(max_retries=5)
    def parents(self, fileId):
        # need to update to work with TeamDrive
        """get a file's parents.

        Args:
            fileId: ID of the file to print parents for.
        
        raises GDriveError
        """
        self.logger.debug('checking parents for item id: {}'.format(fileId))
        apiString = 'fileId={}, fields="parents"'.format(fileId)
        self.logger.debug('api call: {}'.format(apiString))
        try:
            parents = self.service.files().get(supportsTeamDrives=True,fileId=fileId, fields='parents').execute()
        except errors.HttpError as e:
            if e.resp.status in [404]:
                self.logger.info('file/folder not found')
                return(None)
            else:
                self.logger.error(e)
                raise GDriveError(e)
        
        return(parents)

    
    def rm(self):
        pass
    
    @retryer(max_retries=5)
    def getuserinfo(self):
        try:
            user = self.service.about().get(fields='user').execute()
        except errors.HttpError as e:
            self.logger.error(e)
            raise GDriveError(e)
            return(none)
        
        self.userinfo = user['user']
        return(user['user'])
    
    @retryer(max_retries=5)
    def listTeamDrives(self, pageSize=50):
        '''
        List first page of team drives available to the user 
            raises GDriveError
        
            accepts:
                pageSize (int) - items to include in result
            
            returns: 
                dictonary of first page of TeamDrives and capabilities
        '''
        fields = ['teamDrives']
       
        
        try:
            result = self.service.teamdrives().list(pageSize=pageSize, fields=','.join(fields)).execute()
        except errors.HttpError as e:
            self.logger.error(e)
            raise GDriveError(e)
            return(None)
        
        self.teamdrives = result['teamDrives']
        return(result['teamDrives'])




# In[60]:


# # create an instance for testing
# from auth import *
# from pathlib import Path
# logger = logging.getLogger(__name__)
# logging.getLogger().setLevel(logging.DEBUG)
# credential_store = Path('./credentials')
# clientSecrets = '../resources/client_secrets.json'

# credentials = getCredentials(storage_path=credential_store, client_secret=clientSecrets)


# myDrive = googledrive(credentials)


