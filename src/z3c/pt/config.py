import os
from os.path import abspath

DEBUG_MODE_KEY = 'Z3C_PT_DEBUG'
DEBUG_MODE = os.environ.get(DEBUG_MODE_KEY, 'false')
DEBUG_MODE = DEBUG_MODE.lower() in ('yes', 'true', 'on')

PROD_MODE = not DEBUG_MODE

FILECACHE_KEY = 'Z3C_PT_FILECACHE'
FILECACHE = os.environ.get(FILECACHE_KEY, None)
if FILECACHE is not None:
    FILECACHE = abspath(FILECACHE)

DISABLE_I18N_KEY = 'Z3C_PT_DISABLE_I18N'
DISABLE_I18N = os.environ.get(DISABLE_I18N_KEY, 'false')
DISABLE_I18N = DISABLE_I18N.lower() in ('yes', 'true', 'on')
