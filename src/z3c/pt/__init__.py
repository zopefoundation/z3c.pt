# See http://peak.telecommunity.com/DevCenter/setuptools#namespace-packages
try:
    __import__('pkg_resources').declare_namespace(__name__)
except ImportError:
    from pkgutil import extend_path
    __path__ = extend_path(__path__, __name__)

# Fix a Python 3 bug in Chameleon.
import chameleon.i18n
import six
chameleon.i18n.basestring = six.string_types
