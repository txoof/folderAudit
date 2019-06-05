#!/usr/bin/env ipython
#!/usr/bin/env python
# coding: utf-8


# In[94]:


#get_ipython().magic(u'load_ext autoreload')
#get_ipython().magic(u'autoreload 2')

#get_ipython().magic(u'alias nbconvert nbconvert basics.ipynb')




# In[95]:


#get_ipython().magic(u'nbconvert')




# In[75]:


from pathlib import Path
import logging
import logging.config
import configuration

import os




# In[40]:


def resource_path(relative_path):
    '''
    Get the absolute path for a given relative path
    '''
    return Path('.').absolute() / Path(relative_path)




# In[46]:


def fileToList(inputfile, stripWhitespace=True):
    '''
    Creates a list from a text file and optionally strips out whitespace
    this is useful for converting a text file into a list for printingd
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




# In[61]:


def setup_logging(
    default_config=None,
    default_level=logging.INFO,
    output_path='~/', 
    env_key='LOG_CFG'):
    """Setup logging configuration
    borrowed from: https://fangpenlin.com/posts/2012/08/26/good-logging-practice-in-python/
    uses logging configuration json file
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




# In[90]:


def getConfiguration(cfgfile=None, config_required={'Main': {'key1': 'value1', 'key2': 'value2'}}):
    '''
    read an ini configuration file and return a dictionary of key/value pairs
    update configuration file if missing any sections
    accepts: 
        cfgfile - path to configuration file
        config_required - nested dictionary in the following format:
        {'Section1':
            {'key1': 'value1', 'key2': 'value2'},
            
         'Section 2':
            {'key1': 'value1'}
        }
    '''
    if not cfgfile:
        raise ValueError('no configuration file specified')
    # required configuraiton options
    # Section: {'option': 'default value'}
    logger = logging.getLogger(__name__)
    logger.debug('getting configuration from file: {}'.format(cfgfile))
    cfgpath = os.path.dirname(cfgfile)
#     config_required = {
#         'Main': {'credentials': os.path.join(cfgpath, 'credentials/'), 
#                  },
#         }

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


