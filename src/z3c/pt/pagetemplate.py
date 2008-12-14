import os
import sys

from zope import i18n
from chameleon.zpt import template

import language

class BaseTemplate(template.PageTemplate):
    default_parser = language.Parser()

    def bind(self, ob, request=None, macro=None, global_scope=True):
        def render(target_language=None, **kwargs):
            context = self._pt_get_context(ob, request, kwargs)

            if target_language is None:
                try:
                    target_language = i18n.negotiate(
                        request or context.get('request'))
                except:
                    target_language = None

            context['target_language'] = target_language

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
            nothing=None)

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

class PageTemplate(BaseTemplate):
    """Page Templates using TAL, TALES, and METAL.

    This class is suitable for standalone use or class
    property. Keyword-arguments are passed into the template as-is.

    Initialize with a template string."""

    def __get__(self, instance, type):
        return self.bind(instance)

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
        return dict(
            view=view,
            context=kwargs.get('context', view.context),
            request=request or kwargs.get('request', view.request),
            template=self,
            options=kwargs,
            nothing=None)

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
