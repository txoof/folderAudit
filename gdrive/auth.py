#!/usr/bin/env ipython
#!/usr/bin/env python
# coding: utf-8


# In[11]:


#get_ipython().magic(u'alias nbconvert nbconvert auth.ipynb')




# In[12]:


#get_ipython().magic(u'nbconvert')




# In[13]:


import logging
import os

# import google_auth_oauthlib
# import google_auth_httplib2


from oauth2client import file, client, tools
from oauth2client.file import Storage
import httplib2

def getCredentials(storage_path = os.path.expanduser('./'), 
                   client_secret = './client_secrets.json'):
    '''
    creates a google oath2 credential object
    
    getCredentials(storage_path, client_secret)
    Accepts:
        storage_path (string): path to cache credentials
        client_secret (string): path to client_secrets.json
        
    Returns:
        oauth2client.tools.run_flow() credential object
    '''
    
    logger = logging.getLogger(__name__)
    
    # see https://developers.google.com/drive/api/v3/about-auth for complete list of scopes
    scopes = 'https://www.googleapis.com/auth/drive' 
    
    credential_dir = os.path.expanduser(storage_path)
    credential_file = os.path.expanduser(os.path.join(credential_dir, 'credentials.json'))
    flags = tools.argparser.parse_args([])

    logger.debug('preparing google drive credentials')
    
    if not os.path.exists(client_secret):
        logging.critical('fatal error - missing client secret file: {}'.format(client_secret))
        logging.critical('obtain a client secret file at the path specified below')
        logging.critical('filename: {}'.format(client_secret))
        logging.critical('instructions: https://developers.google.com/drive/v3/web/quickstart/python')
        
    logging.debug('checking for credential store directory: {}'.format(credential_dir))
    if not os.path.exists(credential_dir):
        try:
            os.makedirs(credential_dir)
        except (IOError, OSError) as e:
            logging.critical(e)
    
    store = Storage(credential_file)
    creds = store.get()
    
    
    if not creds or creds.invalid:
        logging.debug('credential store not found or is invalid; refreshing')
        flow = client.flow_from_clientsecrets(client_secret, scopes)
        logging.debug('preparing to set store')
        creds = tools.run_flow(flow, store, flags)
    else:
        logging.debug('credential store accepted')
        
    
    return(creds)


