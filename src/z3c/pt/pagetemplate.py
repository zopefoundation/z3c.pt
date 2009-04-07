import os
import sys
import compiler

from zope import i18n
from zope import component

from chameleon.core import types
from chameleon.core import config
from chameleon.core import codegen
from chameleon.core import clauses
from chameleon.core import generation
from chameleon.core import utils

from chameleon.zpt import template
from chameleon.zpt.interfaces import IExpressionTranslator

from z3c.pt import language

_marker = object()
_expr_cache = {}

def evaluate_expression(pragma, expr):
    key = "%s(%s)" % (pragma, expr)
    try:
        symbol_mapping, parts, source = _expr_cache[key]
    except KeyError:
        translator = component.getUtility(IExpressionTranslator, name=pragma)
        parts = translator.tales(expr)
        stream = generation.CodeIO(symbols=config.SYMBOLS)
        assign = clauses.Assign(parts, 'result')
        assign.begin(stream)
        assign.end(stream)
        source = stream.getvalue()

        symbol_mapping = parts.symbol_mapping.copy()
        if isinstance(parts, types.parts):
            for value in parts:
                symbol_mapping.update(value.symbol_mapping)    

        _expr_cache[key] = symbol_mapping, parts, source

    # acquire template locals and update with symbol mapping
    frame = sys._getframe()
    while frame.f_locals.get('econtext', _marker) is _marker:
        frame = frame.f_back
        if frame is None:
            raise RuntimeError, "Can't locate template frame."

    _locals = frame.f_locals
    _locals.update(symbol_mapping)
    
    # to support dynamic scoping (like in templates), we must
    # transform the code to take the scope locals into account; for
    # efficiency, this is cached for reuse
    code_cache_key = key, tuple(_locals)
    try:
        code = _expr_cache[code_cache_key]
    except KeyError:
        suite = codegen.Suite(source, _locals)
        code = compiler.compile(
            suite.source, 'dynamic_path_expression.py', 'exec')
        _expr_cache[code_cache_key] = code

    # execute code and return evaluation
    exec code in codegen.lookup_globals.copy(), _locals
    return _locals['result']

def evaluate_path(expr):
    return evaluate_expression('path', expr)

def evaluate_exists(expr):
    try:
        return evaluate_expression('exists', expr)
    except NameError:
        return False

class BaseTemplate(template.PageTemplate):
    content_type = None
    default_parser = language.Parser()
    version = 2
    
    def bind(self, ob, request=None, macro=None, global_scope=True):
        def render(target_language=None, request=request, **kwargs):
            context = self._pt_get_context(ob, request, kwargs)
            request = request or context.get('request')
            if target_language is None:
                try:
                    target_language = i18n.negotiate(request)
                except:
                    target_language = None

            context['target_language'] = target_language
            context["econtext"] = utils.econtext(context)

            if request is not None and not isinstance(request, basestring):
                content_type = self.content_type or 'text/html'
                if not request.response.getHeader("Content-Type"):
                    request.response.setHeader(
                        "Content-Type", content_type)

            if macro is None:
                return self.render(**context)
            else:
                return self.render_macro(
                    macro, global_scope=global_scope, parameters=context)

        return BoundPageTemplate(self, render)

    def __call__(self, _ob=None, **kwargs):
        bound_pt = self.bind(_ob)
        return bound_pt(**kwargs)

    def _pt_get_context(self, instance, request, kwargs):
        return dict(
            options=kwargs,
            request=request,
            template=self,
            path=evaluate_path,
            exists=evaluate_exists,
            nothing=None,
            modules=sys.modules)

class BaseTemplateFile(BaseTemplate, template.PageTemplateFile):
    """If ``filename`` is a relative path, the module path of the
    class where the instance is used to get an absolute path."""

    def __init__(self, filename, path=None, content_type=None, **kwargs):
        if path is not None:
            filename = os.path.join(path, filename)

        if not os.path.isabs(filename):	       
            for depth in (1, 2):	       
                frame = sys._getframe(depth)	 
                package_name = frame.f_globals['__name__']	 
 	 
                if package_name != self.__module__:	 
                    break	 
 	 
            module = sys.modules[package_name]
            try:	 
                path = module.__path__[0]	 
            except AttributeError:	 
                path = module.__file__	 
                path = path[:path.rfind(os.sep)]	 
 	 
            filename = path + os.sep + filename

        template.PageTemplateFile.__init__(
            self, filename, **kwargs)

        # Set content-type last, so that we can override whatever was
        # magically sniffed from the source template.
        self.content_type = content_type

class PageTemplate(BaseTemplate):
    """Page Templates using TAL, TALES, and METAL.

    This class is suitable for standalone use or class
    property. Keyword-arguments are passed into the template as-is.

    Initialize with a template string."""

    version = 1
    
    def __get__(self, instance, type):
        if instance is not None:
            return self.bind(instance)
        return self
    
class PageTemplateFile(BaseTemplateFile, PageTemplate):
    """Page Templates using TAL, TALES, and METAL.

    This class is suitable for standalone use or class
    property. Keyword-arguments are passed into the template as-is.

    Initialize with a filename."""

class ViewPageTemplate(PageTemplate):
    """Template class suitable for use with a Zope browser view; the
    variables ``view``, ``context`` and ``request`` variables are
    brought in to the local scope of the template automatically, while
    keyword arguments are passed in through the ``options``
    dictionary. Note that the default expression type for this class
    is 'path' (standard Zope traversal)."""
    
    def _pt_get_context(self, view, request, kwargs):
        context = kwargs.get('context')
        if context is None:
            context = view.context
        request = request or kwargs.get('request') or view.request
        return dict(
            view=view,
            context=context,
            request=request,
            template=self,
            path=evaluate_path,
            exists=evaluate_exists,
            options=kwargs,
            nothing=None,
            modules=sys.modules)

    def __call__(self, _ob=None, context=None, request=None, **kwargs):
        kwargs.setdefault('context', context)
        kwargs.setdefault('request', request)
        return super(ViewPageTemplate, self).__call__(
            _ob=_ob, **kwargs)

class ViewPageTemplateFile(ViewPageTemplate, PageTemplateFile):
    """If ``filename`` is a relative path, the module path of the
    class where the instance is used to get an absolute path."""

class BoundPageTemplate(object):
    """When a page template class is used as a property, it's bound to
    the class instance on access, which is implemented using this
    helper class."""
    
    def __init__(self, pt, render):
        object.__setattr__(self, 'im_self', pt)
        object.__setattr__(self, 'im_func', render)
        
    macros = property(lambda self: self.im_self.macros)
    filename = property(lambda self: self.im_self.filename)

    def __call__(self, *args, **kw):
        return self.im_func(**kw)

    def __setattr__(self, name, v):
        raise AttributeError("Can't set attribute", name)

    def __repr__(self):
        return "<%s.Bound%s %r>" % (
            type(self.im_self).__module__,
            type(self.im_self).__name__, self.filename)
