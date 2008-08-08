import os

DEBUG_MODE_KEY = 'Z3C_PT_DEBUG'
DEBUG_MODE = os.environ.get(DEBUG_MODE_KEY, 'false')
DEBUG_MODE = DEBUG_MODE.lower() in ('yes', 'true', 'on')

PROD_MODE = not DEBUG_MODE

DISABLE_I18N_KEY = 'Z3C_PT_DISABLE_I18N'
DISABLE_I18N = os.environ.get(DISABLE_I18N_KEY, 'false')
DISABLE_I18N = DISABLE_I18N.lower() in ('yes', 'true', 'on')

XML_NS = "http://www.w3.org/1999/xhtml"
TAL_NS = "http://xml.zope.org/namespaces/tal"
I18N_NS = "http://xml.zope.org/namespaces/i18n"
PY_NS = "http://genshi.edgewall.org"
NS_MAP = dict(py=PY_NS, tal=PY_NS)
            
        
