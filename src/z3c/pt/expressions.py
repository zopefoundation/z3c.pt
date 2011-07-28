import re
import ast
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

from types import MethodType

from chameleon.tales import PathExpr as BasePathExpr
from chameleon.tales import ExistsExpr as BaseExistsExpr
from chameleon.tales import PythonExpr as BasePythonExpr
from chameleon.codegen import template
from chameleon.astutil import load
from chameleon.astutil import Symbol
from chameleon.astutil import Static
from chameleon.astutil import NameLookupRewriteVisitor
from chameleon.exc import ExpressionError

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
                ns_used = ':' in name
                if ns_used:
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
                    if ns_used and isinstance(base, MethodType):
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


class PathExpr(BasePathExpr):
    path_regex = re.compile(
        r'^(?:(nocall|not):\s*)*((?:[A-Za-z_][A-Za-z0-9_:]*)' +
        r'(?:/[?A-Za-z_@\-+][?A-Za-z0-9_@\-\.+/:]*)*)$')

    interpolation_regex = re.compile(
        r'\?[A-Za-z][A-Za-z0-9_]+')

    traverser = Static(
        template("cls()", cls=Symbol(ZopeTraverser), mode="eval")
        )

    def translate(self, string, target):
        """
        >>> from chameleon.tales import test
        >>> test(PathExpr('')) is None
        True
        """

        string = string.strip()

        if not string:
            return template("target = None", target=target)

        m = self.path_regex.match(string)
        if m is None:
            raise ExpressionError("Not a valid path-expression.", string)

        nocall, path = m.groups()

        # note that unicode paths are not allowed
        parts = str(path).split('/')

        components = []
        for part in parts[1:]:
            interpolation_args = []

            def replace(match):
                start, end = match.span()
                interpolation_args.append(
                    part[start + 1:end])
                return "%s"

            while True:
                part, count = self.interpolation_regex.subn(replace, part)
                if count == 0:
                    break

            if len(interpolation_args):
                component = template(
                    "format % args", format=ast.Str(part),
                    args=ast.Tuple(
                        list(map(load, interpolation_args)),
                        ast.Load()
                        ),
                    mode="eval")
            else:
                component = ast.Str(part)

            components.append(component)

        base = parts[0]

        if not components:
            if len(parts) == 1 and (nocall or base == 'None'):
                return template("target = base", base=base, target=target)
            else:
                components = ()

        call = template(
            "traverse(base, request, call)",
            traverse=self.traverser,
            base=load(base),
            call=load(str(not nocall)),
            mode="eval",
            )

        if components:
            call.args.extend(components)

        return template("target = value", target=target, value=call)


class NocallExpr(PathExpr):
    """A path-expression which does not call the resolved object."""

    def translate(self, expression, engine):
        return super(NocallExpr, self).translate(
            "nocall:%s" % expression, engine)


class ExistsExpr(BaseExistsExpr):
    exceptions = AttributeError, LookupError, TypeError, KeyError, NameError

    def __init__(self, expression):
        super(ExistsExpr, self).__init__("nocall:" + expression)


class ProviderExpr(object):
    provider_regex = re.compile(r'^[A-Za-z][A-Za-z0-9_\.-]*$')

    traverser = Static(
        template("cls()", cls=Symbol(ContentProviderTraverser), mode="eval")
        )

    def __init__(self, expression):
        self.expression = expression

    def __call__(self, target, engine):
        string = self.expression.strip()
        if self.provider_regex.match(string) is None:
            raise SyntaxError(
                "%s is not a valid content provider name." % string)

        return template(
            "target = traverse(context, request, view, name)",
            target=target,
            traverse=self.traverser,
            name=ast.Str(string),
            )


class PythonExpr(BasePythonExpr):
    builtins = {
        'path': template("tales(econtext, rcontext, 'path')", mode="eval"),
        'exists': template("tales(econtext, rcontext, 'exists')", mode="eval"),
        }

    def __init__(self, expression):
        self.expression = expression

    def __call__(self, target, engine):
        return self.translate(self.expression, target)

    def rewrite(self, node):
        return self.builtins.get(node.id, node)

    @property
    def transform(self):
        return NameLookupRewriteVisitor(self.rewrite)
