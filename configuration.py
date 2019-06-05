#!/usr/bin/env ipython
#!/usr/bin/env python
# coding: utf-8


# In[1]:


#get_ipython().magic(u'alias nbconvert nbconvert configuration.ipynb')




# In[2]:


#get_ipython().magic(u'nbconvert')




# In[1]:


import logging
import configparser
from configparser import NoOptionError
import os




# In[6]:


# borrowed from: https://www.blog.pythonlibrary.org/2013/10/25/python-101-an-intro-to-configparser/
def create_config(path, configuration):
    '''
    create a configuration file at <path>
    Accepts:
        configuration in the format {'SectionName': {'key1':'value', 'key2':'value'}, 'OtherSection' {'opt1':'value', 'opt2':'Value'}}
    
    Note: SafeConfigParser treats all values as string 
    '''
    logger = logging.getLogger(__name__)
    cfgfile = os.path.expanduser(path)
    cfgpath = os.path.dirname(os.path.expanduser(path))
        
    if not os.path.exists(cfgpath):
        logger.info('creating configuration path: {path}')
        try:
            os.makedirs(cfgpath)
        except Exception as e:
            logger.error(e)
  
    try:
        logger.info('writing configuration file: {}'.format(cfgfile))
#         with open(cfgfile, 'wb') as config_file:
        with open(cfgfile, 'w') as config_file:
            configuration.write(config_file)
    except Exception as e:
        logger.error(e)

def get_config(path):
    '''
    fetch configuration as a configuration object
    '''
    logger = logging.getLogger(__name__)
    cfgfile = os.path.expanduser(path)
    cfgpath = os.path.dirname(os.path.expanduser(path))
    config = configparser.SafeConfigParser()

    if not os.path.isfile(cfgfile):
        logger.warn('no configuration file found at: {}'.format(cfgfile))
        logger.info('returning empty config object')
        return config
    else:
        logger.debug('reading configuration file at: {}'.format(cfgfile))
        config.read(path)
        return config



def get_setting(path, section, setting):
    '''
    get the requested from section
    '''
    logger = logging.getLogger(__name__)
    cfgfile = os.path.expanduser(path)
    config = get_config(path)
    try:
        value = config.get(section, setting)
        return(value)
    except NoOptionError as e:
        logging.warn('option not found: {}'.format(setting))
        return('')
        

# def update_setting(path, section, setting, value):
#     '''
#     update an option
#     '''
#     logger = logging.getLogger(__name__)
#     config = get_config(config)
#     config.set(section, setting, value)
#     try:
#         with open(path, 'wb') as config_file:
#             config.write(config_file)
#     except Exception as e:
#         logging.error(e)


