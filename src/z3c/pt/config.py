import os

DEBUG_MODE = os.environ.get('Z3C_PT_DEBUG', 'false')
DEBUG_MODE = DEBUG_MODE.lower() in ('yes', 'true', 'on')

PROD_MODE = not DEBUG_MODE
