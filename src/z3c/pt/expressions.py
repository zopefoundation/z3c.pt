import re
import namespaces
import zope.event

from zope.traversing.adapters import traversePathElement
from zope.contentprovider.interfaces import IContentProvider
from zope.contentprovider.interfaces import ContentProviderLookupError
from zope.traversing.interfaces import ITraversable

try:
    from zope.contentprovider.interfaces import BeforeUpdateEvent
except ImportError:
    BeforeUpdateEvent = None

from chameleon.core import types
from chameleon.zpt import expressions
from chameleon.zpt.interfaces import IExpressionTranslator

from types import MethodType

_marker = object()
_valid_name = re.compile(r"[a-zA-Z][a-zA-Z0-9_]*$").match

def identity(x):
    return x

class ContentProviderTraverser(object):
    def __call__(self, context, request, view, name):
        cp = zope.component.queryMultiAdapter(
            (context, request, view), IContentProvider, name=name)

        # provide a useful error message, if the provider was not found.
        if cp is None:
            raise ContentProviderLookupError(name)

        if BeforeUpdateEvent is not None:
            zope.event.notify(BeforeUpdateEvent(cp, request))
        cp.update()
        return cp.render()

class ZopeTraverser(object):
    def __init__(self, proxify=identity):
        self.proxify = proxify

    def __call__(self, base, request, call, *path_items):
        """See ``zope.app.pagetemplate.engine``."""

        if bool(path_items):
            path_items = list(path_items)
            path_items.reverse()

            while len(path_items):
                name = path_items.pop()
                ns = ':' in name
                if ns is True:
                    namespace, name = name.split(':', 1)
                    base = namespaces.function_namespaces[namespace](base)
                    if ITraversable.providedBy(base):
                        base = self.proxify(traversePathElement(
                            base, name, path_items, request=request))
                        continue

                # special-case dicts for performance reasons
                if isinstance(base, dict):
                    next = base.get(name, _marker)
                else:
                    next = getattr(base, name, _marker)

                if next is not _marker:
                    base = next
                    if ns is True and isinstance(base, MethodType):
                        base = base()
                    continue
                else:
                    base = traversePathElement(
                        base, name, path_items, request=request)

                if not isinstance(base, (basestring, tuple, list)):
                    base = self.proxify(base)

        if call and getattr(base, '__call__', _marker) is not _marker:
            return base()

        return base

class ZopeExistsTraverser(ZopeTraverser):
    exceptions = AttributeError, LookupError, TypeError

    def __call__(self, base, request, call, *args, **kwargs):
        try:
            return ZopeTraverser.__call__(
                self, base, request, False, *args, **kwargs) is not None
        except self.exceptions:
            return False
        return True

class PathTranslator(expressions.ExpressionTranslator):
    path_regex = re.compile(
        r'^((nocall|not):\s*)*([A-Za-z_][A-Za-z0-9_:]*)'+
        r'(/[?A-Za-z_@\-+][?A-Za-z0-9_@\-\.+/:]*)*$')

    interpolation_regex = re.compile(
        r'\?[A-Za-z][A-Za-z0-9_]+')

    path_traverse = ZopeTraverser()
    scope = 'request'

    symbol = '_path'

    def translate(self, string, escape=None):
        """
        >>> translate = PathTranslator().translate

        >>> translate("") is None
        True

        >>> translate("nocall: a")
        value('a')

        >>> translate("nothing")
        value('None')

        >>> translate("a/b")
        value("_path(a, request, True, 'b')")

        Verify allowed character set.

        >>> translate("image_path/++res++/@@hello.html")
        value("_path(image_path, request, True, '++res++', '@@hello.html')")

        >>> translate("context/@@view")
        value("_path(context, request, True, '@@view')")

        >>> translate("nocall: context/@@view")
        value("_path(context, request, False, '@@view')")

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

        while string:
            m = self.re_pragma.match(string)
            if m is None:
                break

            string = string[m.end():]
            pragma = m.group('pragma').lower()

            if pragma == 'nocall':
                nocall = True
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
                component = repr(str(part))

            components.append(component)

        base = parts[0]

        if not components:
            if len(parts) == 1 and (nocall or base == 'None'):
                value = types.value('%s' % base)
                return value
            else:
                components = ()

        value = types.value(
            '%s(%s, %s, %s, %s)' % \
            (self.symbol, base, self.scope, not nocall, ', '.join(components)))

        value.symbol_mapping[self.symbol] = self.path_traverse

        return value

class NotTranslator(expressions.ExpressionTranslator):
    zope.component.adapts(IExpressionTranslator)

    recursive = True

    def __init__(self, translator):
        self.translator = translator

    def tales(self, string, escape=None):
        """
        >>> tales = NotTranslator(path_translator).tales

        >>> tales("abc/def/ghi")
        value("not(_path(abc, request, True, 'def', 'ghi'))")

        >>> tales("abc | def")
        parts(value('not(_path(abc, request, True, ))'),
              value('not(_path(def, request, True, ))'))

        >>> tales("abc | not: def")
        parts(value('not(_path(abc, request, True, ))'),
              value('not(not(_path(def, request, True, )))'))

        >>> tales("abc | not: def | ghi")
        parts(value('not(_path(abc, request, True, ))'),
              value('not(not(_path(def, request, True, )))'),
              value('not(not(_path(ghi, request, True, )))'))
        """

        value = self.translator.tales(string, escape=escape)
        if isinstance(value, types.value):
            value = (value,)

        parts = []
        for part in value:
            factory = type(part)
            value = factory("not(%s)" % part)
            value.symbol_mapping.update(part.symbol_mapping)
            parts.append(value)

        if len(parts) == 1:
            return parts[0]

        return types.parts(parts)

class ProviderTranslator(expressions.ExpressionTranslator):
    provider_regex = re.compile(r'^[A-Za-z][A-Za-z0-9_\.-]*$')

    symbol = '_get_content_provider'
    content_provider_traverser = ContentProviderTraverser()

    def translate(self, string, escape=None):
        if self.provider_regex.match(string) is None:
            raise SyntaxError(
                "%s is not a valid content provider name." % string)

        value = types.value("%s(context, request, view, '%s')" % \
                            (self.symbol, string))
        value.symbol_mapping[self.symbol] = self.content_provider_traverser
        return value

class ExistsTranslator(PathTranslator):
    """Implements string translation expression."""

    symbol = '_path_exists'

    path_traverse = ZopeExistsTraverser()

    def translate(self, *args, **kwargs):
        value = super(ExistsTranslator, self).translate(*args, **kwargs)
        if value is None:
            return

        assert isinstance(value, types.value)
        parts = types.parts(
            (value, types.value('False')))
        parts.exceptions = NameError,
        return parts

exists_translator = ExistsTranslator()
path_translator = PathTranslator()
provider_translator = ProviderTranslator()
