import sys
import logging
import config

from UserDict import UserDict

# check if we're able to coerce unicode to str
try:
    str(u'La Pe\xf1a')
    unicode_required_flag = False
except UnicodeEncodeError:
    unicode_required_flag = True
    log = logging.getLogger('z3c.pt')
    log.info("Default system encoding is set to '%s'; "
             "the template engine will perform better if "
             "an encoding that coerces gracefully to "
             "unicode is used ('utf-8' recommended)." % sys.getdefaultencoding())

s_counter = 0

def handler(key=None):
    def decorate(f):
        def g(node):
            if key is None:
                return f(node, None)
            return f(node, node.get(key))
        g.__ns__ = key
        return g
    return decorate

def attribute(ns, factory=None, default=None):
    def get(self):
        value = self.attrib.get(ns)
        if value is not None:
            if factory is None:
                return value
            f = factory(self.translator)
            return f(value)
        elif default is not None:
            return default
    def set(self, value):
        self.attrib[ns] = value
    return property(get, set)

class scope(list):
    def __init__(self, *args):
        global s_counter
        self.hash = s_counter
        s_counter += 1

    def __hash__(self):
        return self.hash

class emptydict(dict):
    def __setitem__(self, key, value):
        raise TypeError("Read-only dictionary does not support assignment.")
    
class repeatitem(object):
    def __init__(self, iterator, length):
        self.length = length
        self.iterator = iterator
        
    @property
    def index(self):
        try:
            length = len(self.iterator)
        except TypeError:
            length = self.iterator.__length_hint__()
        except:
            raise TypeError("Unable to determine length.")

        try:
            return self.length - length - 1
        except TypeError:
            return None
            
    @property
    def start(self):
        return self.index == 0

    @property
    def end(self):
        return self.index == self.length - 1

    def number(self):
        return self.index + 1

    def odd(self):
        return bool(self.index % 2)

    def even(self):
        return not self.odd()

class repeatdict(dict):
    def insert(self, key, iterable):
        try:
            length = len(iterable)
        except TypeError:
            length = None
            
        try:
            # We used to do iterable.__iter__() but, e.g. BTreeItems
            # objects are iterable (via __getitem__) but don't possess
            # an __iter__.  call iter(iterable) instead to determine
            # iterability.
            iterator = iter(iterable)
        except TypeError:
            raise TypeError(
                "Can only repeat over an iterable object (%s)." % iterable)
        
        self[key] = (iterator, length)
        return iterator
        
    def __getitem__(self, key):
        value, length = dict.__getitem__(self, key)

        if not isinstance(value, repeatitem):
            value = repeatitem(value, length)
            self[key] = (value, length)
            
        return value

class odict(UserDict):
    def __init__(self, dict = None):
        self._keys = []
        UserDict.__init__(self, dict)

    def __delitem__(self, key):
        UserDict.__delitem__(self, key)
        self._keys.remove(key)

    def __setitem__(self, key, item):
        UserDict.__setitem__(self, key, item)
        if key in self._keys:
            self._keys.remove(key)
        self._keys.append(key)

    def clear(self):
        UserDict.clear(self)
        self._keys = []

    def copy(self):
        dict = UserDict.copy(self)
        dict._keys = self._keys[:]
        return dict

    def items(self):
        return zip(self._keys, self.values())

    def keys(self):
        return self._keys

    def popitem(self):
        try:
            key = self._keys[-1]
        except IndexError:
            raise KeyError('dictionary is empty')

        val = self[key]
        del self[key]

        return (key, val)

    def setdefault(self, key, failobj = None):
        UserDict.setdefault(self, key, failobj)
        if key not in self._keys: self._keys.append(key)

    def update(self, dict):
        UserDict.update(self, dict)
        for key in dict.keys():
            if key not in self._keys: self._keys.append(key)

    def values(self):
        return map(self.get, self._keys)
    
def get_attributes_from_namespace(element, namespace):
    if element.nsmap.get(element.prefix) == namespace:
        return dict([
            (name, value) for (name, value) in element.attrib.items() \
            if '{' not in name])

    return dict([
        (name, value) for (name, value) in element.attrib.items() \
        if name.startswith('{%s}' % namespace)])

def get_namespace(element):
    if '}' in element.tag:
        return element.tag.split('}')[0][1:]
    return element.nsmap[None]

def xhtml_attr(name):
    return "{%s}%s" % (config.XHTML_NS, name)

def tal_attr(name):
    return "{%s}%s" % (config.TAL_NS, name)

def meta_attr(name):
    return "{%s}%s" % (config.META_NS, name)

def metal_attr(name):
    return "{%s}%s" % (config.METAL_NS, name)

def i18n_attr(name):
    return "{%s}%s" % (config.I18N_NS, name)

def py_attr(name):
    return "{%s}%s" % (config.PY_NS, name)
