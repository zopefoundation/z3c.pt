import parser
import re

import zope.interface
import zope.component

from zope.traversing.adapters import traversePathElement
from zope.contentprovider.interfaces import IContentProvider
from zope.contentprovider.interfaces import ContentProviderLookupError

from chameleon.core import types
from chameleon.zpt import expressions
from chameleon.zpt.interfaces import IExpressionTranslator

_marker = object()

def identity(x):
    return x

def get_content_provider(context, request, view, name):
    cp = zope.component.queryMultiAdapter(
        (context, request, view), IContentProvider, name=name)

    # provide a useful error message, if the provider was not found.
    if cp is None:
        raise ContentProviderLookupError(name)

    cp.update()
    return cp.render()

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
    
class ZopeExistsTraverser(ZopeTraverser):
    exceptions = AttributeError, LookupError, TypeError
    
    def __call__(self, *args, **kwargs):
        try:
            return ZopeTraverser.__call__(self, *args, **kwargs)
        except self.exceptions:
            return 0
        return 1

class PathTranslator(expressions.ExpressionTranslator):
    path_regex = re.compile(
        r'^((nocall|not):\s*)*([A-Za-z_][A-Za-z0-9_]*)'+
        r'(/[?A-Za-z_@\-+][?A-Za-z0-9_@\-\.+/]*)*$')

    interpolation_regex = re.compile(
        r'\?[A-Za-z][A-Za-z0-9_]+')

    path_traverse = ZopeTraverser()

    symbol = '_path'

    def translate(self, string, escape=None):
        """
        >>> translate = PathTranslator().translate

        >>> translate("") is None
        True

        >>> translate("a/b")
        value("_path(a, request, True, 'b')")

        Verify allowed character set.

        >>> translate("image_path/++res++/@@hello.html")
        value("_path(image_path, request, True, '++res++', '@@hello.html')")
        
        >>> translate("context/@@view")
        value("_path(context, request, True, '@@view')")

        >>> translate("nocall: context/@@view")
        value("_path(context, request, False, '@@view')")

        >>> translate("not: context/@@view")
        value("not(_path(context, request, True, '@@view'))")

        >>> translate("context/?view")
        value("_path(context, request, True, '%s' % (view,))")

        >>> translate("context/@@?view")
        value("_path(context, request, True, '@@%s' % (view,))")
        """

        if not string:
            return None
        
        if not self.path_regex.match(string.strip()):
            raise SyntaxError("Not a valid path-expression: %s." % string)

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

        components = []
        for part in parts[1:]:
            interpolation_args = []

            def replace(match):
                start, end = match.span()
                interpolation_args.append(
                    part[start+1:end])
                return "%s"

            while True:
                part, count = self.interpolation_regex.subn(replace, part)
                if count == 0:
                    break

            if len(interpolation_args):
                component = "%s %% (%s,)" % (
                    repr(part), ", ".join(interpolation_args))
            else:
                component = repr(part)

            components.append(component)
            
        if not components:
            components = ()

        base = parts[0]
        value = types.value(
            '%s(%s, request, %s, %s)' % \
            (self.symbol, base, not nocall, ', '.join(components)))

        if negate:
            value = types.value('not(%s)' % value)

        value.symbol_mapping[self.symbol] = self.path_traverse

        return value

class NotTranslator(PathTranslator):
    symbol = '_path_not'

    def translate(self, string, escape=None):
        path_translator = zope.component.getUtility(
            IExpressionTranslator, name='path')
        value = path_translator.translate(string, escape=escape)
        symbol_mapping = value.symbol_mapping
        value = types.value("not(%s)" % value)
        value.symbol_mapping = symbol_mapping
        return value

class ProviderTranslator(expressions.ExpressionTranslator):
    provider_regex = re.compile(r'^[A-Za-z][A-Za-z0-9_\.-]*$')
    
    symbol = '_get_content_provider'

    def translate(self, string, escape=None):
        if self.provider_regex.match(string) is None:
            raise SyntaxError(
                "%s is not a valid content provider name." % string)

        value = types.value("%s(context, request, view, '%s')" % \
                            (self.symbol, string))
        value.symbol_mapping[self.symbol] = get_content_provider
        return value

class ExistsTranslator(PathTranslator):
    """Implements string translation expression."""

    symbol = '_path_exists'
    
    path_traverse = ZopeExistsTraverser()

exists_translator = ExistsTranslator()
path_translator = PathTranslator()
not_translator = NotTranslator()    
provider_translator = ProviderTranslator()

