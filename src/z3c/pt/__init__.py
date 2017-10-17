__import__('pkg_resources').declare_namespace(__name__)

# Fix a Python 3 bug in Chameleon.
import chameleon.i18n
import six
chameleon.i18n.basestring = six.string_types
