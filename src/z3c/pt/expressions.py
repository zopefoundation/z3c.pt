import parser
import re

import zope.interface
import zope.component

from zope.traversing.adapters import traversePathElement
from zope.contentprovider.interfaces import IContentProvider
from zope.contentprovider.interfaces import ContentProviderLookupError

from chameleon.core import types
from chameleon.zpt import expressions

_marker = object()

def identity(x):
    return x

class ZopeTraverser(object):
    def __init__(self, proxify=identity):
        self.proxify = proxify

    def __call__(self, base, request, call, *path_items):
        """See ``zope.app.pagetemplate.engine``."""

        length = len(path_items)
        if length:
            i = 0
            while i < length:
                name = path_items[i]
                i += 1
                next = getattr(base, name, _marker)
                if next is not _marker:
                    base = next
                    continue
                else:
                    # special-case dicts for performance reasons        
                    if isinstance(base, dict):
                        base = base[name]
                    else:
                        base = traversePathElement(
                            base, name, path_items[i:], request=request)

                if not isinstance(base, (basestring, tuple, list)):
                    base = self.proxify(base)

        if call and getattr(base, '__call__', _marker) is not _marker:
            return base()

        return base

class PathTranslator(expressions.ExpressionTranslator):
    path_regex = re.compile(
        r'^((nocall|not):\s*)*([A-Za-z_][A-Za-z0-9_]*)'+
        r'(/[A-Za-z_@\-+][A-Za-z0-9_@\-\.+/]*)*$')

    path_traverse = ZopeTraverser()

    symbol = '_path'
    
    def validate(self, string):
        """
        >>> validate = PathTranslator().validate
        >>> validate("image_path/++resource++/@@hello.html")
        """

        if not self.path_regex.match(string.strip()):
            raise SyntaxError("Not a valid path-expression.")

    def translate(self, string):
        """
        >>> translate = PathTranslator().translate

        >>> translate("a/b")
        value("_path(a, request, True, 'b')")

        Verify allowed character set.

        >>> translate("context/@@view")
        value("_path(context, request, True, '@@view')")

        >>> translate("nocall: context/@@view")
        value("_path(context, request, False, '@@view')")

        >>> translate("not: context/@@view")
        value("not(_path(context, request, True, '@@view'))")

        """

        nocall = False
        negate = False

        while string:
            m = self.re_pragma.match(string)
            if m is None:
                break

            string = string[m.end():]
            pragma = m.group('pragma').lower()

            if pragma == 'nocall':
                nocall = True
            elif pragma == 'not':
                negate = True
            else:
                raise ValueError("Invalid pragma: %s" % pragma)

        parts = string.strip().split('/')

        # map 'nothing' to 'None'
        parts = map(lambda part: part == 'nothing' and 'None' or part, parts)
        
        base = parts[0]
        components = [repr(part) for part in parts[1:]]

        if not components:
            components = ()

        value = types.value(
            '%s(%s, request, %s, %s)' % \
            (self.symbol, base, not nocall, ', '.join(components)))

        if negate:
            value = types.value('not(%s)' % value)

        value.symbol_mapping[self.symbol] = self.path_traverse

        return value

path_translator = PathTranslator()

def get_content_provider(context, request, view, name):
    cp = zope.component.queryMultiAdapter(
        (context, request, view), IContentProvider, name=name)

    # provide a useful error message, if the provider was not found.
    if cp is None:
        raise ContentProviderLookupError(name)

    cp.update()
    return cp.render()
    
class ProviderTranslator(expressions.ExpressionTranslator):
    provider_regex = re.compile(r'^[A-Za-z][A-Za-z0-9_-]*$')
    symbol = '_get_content_provider'
    
    def validate(self, string):
        if self.provider_regex.match(string) is None:
            raise SyntaxError(
                "%s is not a valid content provider name." % string)

    def translate(self, string):
        value = types.value("%s(context, request, view, '%s')" % \
                            (self.symbol, string))
        value.symbol_mapping[self.symbol] = get_content_provider
        return value
    
provider_translator = ProviderTranslator()
