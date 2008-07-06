import os
from os.path import abspath

DEBUG_MODE = os.environ.get('Z3C_PT_DEBUG', 'false')
DEBUG_MODE = DEBUG_MODE.lower() in ('yes', 'true', 'on')

PROD_MODE = not DEBUG_MODE

FILECACHE = os.environ.get('Z3C_PT_FILECACHE', None)
if FILECACHE is not None:
    FILECACHE = abspath(FILECACHE)
