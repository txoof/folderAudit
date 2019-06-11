#!/usr/bin/env ipython
#!/usr/bin/env python
# coding: utf-8


# In[1]:


#get_ipython().magic(u'load_ext autoreload')
#get_ipython().magic(u'autoreload 2')

#get_ipython().magic(u'alias nbconvert nbconvert folderAudit.ipynb')




# In[2]:


#get_ipython().magic(u'nbconvert')




# In[3]:


import csv
import os
import sys
import logging
import logging.config
import configuration
import textwrap
import csv
import re
import datetime
from humanfriendly import prompts

from googleapiclient import http
from pathlib import Path
from gdrive.auth import getCredentials
from gdrive.gdrive import googledrive, GDriveError




# In[4]:


def resource_path(relative_path):
    """ Get absolute path to resource, works for ide and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)




# In[5]:


def fileToList(inputfile, stripWhitespace=True):
    '''
    Creates a list from a text file and optionally strips out whitespace
    '''
    logger = logging.getLogger(__name__)
    logger.debug('inputfile = {}'.format(inputfile))
#     super elegant solution as seen below 
#     https://stackoverflow.com/questions/4842057/easiest-way-to-ignore-blank-lines-when-reading-a-file-in-python
    try:
        with open(inputfile, 'r') as fhandle:
            if stripWhitespace:
                lines = [_f for _f in (line.strip() for line in fhandle) if _f]
            else:
                lines = [line.strip() for line in fhandle]
    except IOError as e:
        logger.debug(e)
    return(lines)




# In[6]:


def setup_logging(
    default_config=None,
    default_level=logging.INFO,
    output_path='~/', 
    env_key='LOG_CFG'):
    """Setup logging configuration
    borrowed from: https://fangpenlin.com/posts/2012/08/26/good-logging-practice-in-python/

    """
    path = default_config
    value = os.getenv(env_key, None)
    config = None
    if value:
        path = value
    if os.path.exists(path):
        try:
            with open(path, 'rt') as f:
                config = json.load(f)
        except Exception as e:
            print('failed to read logging configuration')
            return(None)

        # set the specific path to store log files
        if config:
            if output_path:
                for handler in config['handlers']:
                    if 'filename' in config['handlers'][handler]:
                        logFile = os.path.basename(config['handlers'][handler]['filename'])
                        logPath = os.path.expanduser(output_path+'/')

                        if not os.path.isdir(logPath):
                            try:
                                os.makedirs(logPath)
                            except OSError as e:
                                logging.error('failed to make log file directory: {}'.format(e))
                                logging.error('using {} instead'.format(config['handlers'][handler]['filename']))
                                break

                        config['handlers'][handler]['filename'] = logPath+logFile


            logging.config.dictConfig(config)
            logging.getLogger().setLevel(default_level)
            return(config)
        else:
            return(None)

    else:
        logging.basicConfig(level=default_level)
        return(None)




# In[7]:


def getConfiguration(cfgfile):
    # required configuraiton options
    # Section: {'option': 'default value'}
    logger = logging.getLogger(__name__)
    logger.debug('getting configuration from file: {}'.format(cfgfile))
    cfgpath = os.path.dirname(cfgfile)
    config_required = {
        'Main': {'credentials': os.path.join(cfgpath, 'credentials/'), 
                 },
        }

    config = configuration.get_config(cfgfile)

    update_config = False

    logger.debug('checking sections')
    for section, values in list(config_required.items()):
        if not config.has_section(section):
            logger.warning('section: {} not found in {}'.format(section, cfgfile))
            logger.debug('adding section {}'.format(section))
            config.add_section(section)
            update_config = True
        for option, value in list(values.items()):
            if not config.has_option(section, option):
                logger.warning('option: {} not found in {}'.format(option, cfgfile))
                logger.debug('adding option {}: {}'.format(option, value))

                config.set(section, option, value)
                update_config = True


    # for section, options in config_required.items():

    if update_config:
        try:
            logger.debug('updating configuration file at: {}'.format(cfgfile))
            configuration.create_config(cfgfile, config)
        except Exception as e:
            logger.error(e)
            
    return(config)




# In[8]:


def doExit(exit_level=0, testing=False):
    logger = logging.getLogger(__name__)
    logger.info('exiting before completion with exit code {}'.format(exit_level))
    if not testing:
        sys.exit(0)




# In[9]:


def recurseFolders(myDrive, parents="", fieldNames='parents, id, name', fileList=[], skipped=[], depth=0):
    if depth == 0:
        fileList = []
        skipped = []
    print('depth: ', depth)
    try:
        result = myDrive.search(parents=parents, fields=fieldNames)
    except GDriveError as e:
        print(e)
        skipped.append(parents)
    for file in result['files']:
        if file['mimeType'] == 'application/vnd.google-apps.folder':
            returnVals = recurseFolders(myDrive=myDrive, parents=file['id'], fieldNames=fieldNames, fileList=fileList, 
                                        skipped=skipped, depth=depth+1)
            fileList + returnVals[0]
            skipped + returnVals[1]
        else:
            fileList.append(file)
    
    return(fileList, skipped)




# In[10]:


def auditFolder(myDrive=None, parents='', name='NO NAME FOLDER'):
    date = datetime.date.today().strftime("%Y-%m-%d")
    outputFile = date+'_'+name+'_Ownership Audit.csv'
    outputPath = Path.home()/'Desktop'/outputFile
    skippedFile = date+name+'_Ownership Audit Skipped Folders.csv'
    skippedPath = Path.home()/'Desktop'/skippedFile
    fieldNames = ['webViewLink', 'owners', 'mimeType', 'name', 'size', 'modifiedTime', 'id']
    
    
    logger = logging.getLogger(__name__)
    logging.getLogger().setLevel(logging.WARNING)
    
    rawResult = recurseFolders(myDrive=myDrive, parents=parents, fieldNames=', '.join(fieldNames))
    allFiles = []
    
    for file in rawResult[0]:
        fileDict = {}
        for field in fieldNames:
            data = ''
            if field == 'owners':
                data = file[field][0]['emailAddress']
            else:
                if field in file:
                    data = file[field]
            fileDict[field] = data

        allFiles.append(fileDict)

    if allFiles:
        with open(outputPath, 'w', newline='') as csvfile:
    #         fieldnames = ['webViewLink', 'owners', 'mimeType', 'name', 'size']
            writer = csv.DictWriter(csvfile, fieldnames=fieldNames)
            writer.writeheader()
            for file in allFiles:
                writer.writerow(file)
    else:
        return None

    # write out skipped folders
    if rawResult[1]:
        logger.warn('Some folders were not included in the audit. See: {}'.format(skippedPath))
        with open(skippedPath, 'w') as skipped:
            for each in rawResult[1]:
                skipped.write(each+'\n')
                
    return(outputPath)
        




# In[11]:


def uploadSheet(myDrive, file):
    # myDrive = googledrive('/Users/aciuffo/.config/folderAudit/credentials/credentials.json')
    file = Path(file)
    file_metadata = {
        'name': file.name,
        'mimeType': 'application/vnd.google-apps.spreadsheet'
    }
    media = http.MediaFileUpload(file,
                            mimetype='text/csv',
                            resumable=True)
    file = myDrive.service.files().create(body=file_metadata,
                                        media_body=media,
                                        fields='id, webViewLink').execute()
    if file:
        print('File uploaded to: {}'.format(file.get('webViewLink')))
    return(file)




# In[21]:


def main():
    testing = True
    version = '00.01 - 2019.05.28'
    appName = 'folderAudit'
    
    cfgfile = appName+'.ini'
    cfgpath = Path.home()/'.config'/appName
    cfgfile = cfgpath/cfgfile

    print('cfgpath', cfgpath)
    
    logger = logging.getLogger(__name__)
    loggingConfig = resource_path('resources/logging.json')
    setup_logging(default_config=loggingConfig, default_level=logging.ERROR, output_path='~/')
    
    
    levelNames = ['DEBUG', 'INFO', 'WARNING']
    
    # configuration 
    myConfig = getConfiguration(cfgfile)    
    updateConfig = False
    
    
    # set the terminal size to 50x90 characters
    print("\x1b[8;50;90t")    
    
    
    # set up configuration
    if myConfig.has_option('Main', 'credentials'):
        credential_store = os.path.expanduser(myConfig.get('Main', 'credentials'))
    else:
        credential_store = os.path.expanduser(os.path.join(cfgpath, 'credentials'))
        updateConfig = True
 
    if myConfig.has_option('Main', 'useremail'):
        useremail = myConfig.get('Main', 'useremail')
    else:
        useremail = None
    
    if myConfig.has_option('Main', 'loglevel'):
        loglevel = myConfig.get('Main', 'loglevel')
        if loglevel in levelNames:
            logger.setLevel(loglevel)
    else:
        loglevel = 'ERROR'
        logger.setLevel(loglevel)
        myConfig.set('Main', 'loglevel', loglevel)
        updateConfig = True

    # print the configuration if the logging level is high enough
    if logging.getLogger().getEffectiveLevel() <= 10:
        config_dict = {}
        for section in myConfig.sections():
            config_dict[section] = {}
            for option in myConfig.options(section):
                config_dict[section][option] = myConfig.get(section, option)

        logger.debug('current configuration:')
        logger.debug('\n{}'.format(config_dict))

    about = resource_path('./resources/about.txt')
    about_list = fileToList(about, False)
    wrapper = textwrap.TextWrapper(replace_whitespace=True, drop_whitespace=True, width=65)
    print(('{} - Version: {}'.format(appName, version)))
    for line in about_list:
        print(('\n'.join(wrapper.wrap(text=line))))
        
    
    logger.setLevel('DEBUG')
        
   # assume that the configuration is NOT ok and that user will want to reconfigure
    proceed = True
    # start with configuration settings from config file; if user chooses to reconfigure offer opportunity to change
    reconfigure = True
    
    # check configuration and credentials for google drive
    clientSecrets = resource_path('resources/client_secrets.json')
    try:
        credentials = getCredentials(storage_path=credential_store, client_secret=clientSecrets)
    except Exception as e:
        logging.critical(e)

    # configure google drive object

    try:
        myDrive = googledrive(credentials)
    except Exception as e:
        logger.error('Could not set up google drive connection: {}'.format(e))
        print('Could not setup google drive connection. Run this program again.')
        print(('If this error persists, please check the logs: {}'.format(log_files)))
        print('cannot continue')
        doExit(testing=testing)

    if not useremail:
        logger.warning('No useremail set in configuration file')
        try:
            useremail = myDrive.userinfo['emailAddress']
        except Exception as e:
            logging.error('Error retreving useremail address from drive configuration')
            print('Error fetching configuration information.')
            print('Run the program again')
            print(('If this error persists, please check the logs: {}'.format(log_files)))
            doExit(testing=testing)
        myConfig.set('Main', 'useremail', useremail)
        updateConfig = True

    if updateConfig:
        configuration.create_config(cfgfile, myConfig)

    while proceed:
        folderURL = prompts.prompt_for_input('Paste full URL of Folder to Audit:\n')
        
        folderName = None
        folderID = None
        
#         match = re.match('https:\/\/drive.google.com(?:\/.*)+\/([a-zA-Z0-9-]+)\W{0,}$', folderURL)
        match = re.match('https:\/\/drive.google.com\/.*(?:\w+\/|=)([a-zA-Z0-9_-]+)', folderURL)
        if not match:
            print('Invlaid URL; try again')
            continue
        else:
            folderID = match[1]
            print('folderID=', folderID)
            
        try:
            result = myDrive.getprops(fileId=folderID, fields="name, mimeType")
        except GDriveError as e:
            logger.error('Trouble getting information for this folder. Try again.')
            logger.error(e)
            continue
        
        if not result['mimeType'] == myDrive.mimeTypes['folder']:
            logger.error('This is is not a folder. Try again.')
            continue
        else:
            print('Beginning audit of folder: {}'.format(result['name']))
            outputFile = auditFolder(myDrive=myDrive, parents=folderID, name=result['name'])
            if outputFile:
                file = uploadSheet(myDrive, outputFile)
            else:
                print('The audit returned no results')
                
        
        if not prompts.prompt_for_confirmation('Would you like to audit another folder?', False):
            proceed = False
            return(file)




# In[22]:


if __name__ == "__main__":
    file = main()
    


