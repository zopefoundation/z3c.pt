import os
import sys

import chameleon.zpt.template
import chameleon.zpt.language

class PageTemplate(chameleon.zpt.template.PageTemplate):
    """Template class suitable for standalone use or as a class
    attribute (property). Keyword-arguments are passed into the
    template as-is."""

    default_parser = chameleon.zpt.language.Parser(default_expression='path')
    
    def bind(self, ob, request=None, macro=None, global_scope=True):
        def render(**kwargs):
            context = self._pt_get_context(ob, request, **kwargs)
            
            if macro is None:
                return self.render(**context)
            else:
                return self.render_macro(
                    macro, global_scope=global_scope, parameters=context)

        return BoundPageTemplate(render, self)

    def __call__(self, _ob=None, **kwargs):
        bound_pt = self.__get__(_ob)
        return bound_pt(**kwargs)

    def _pt_get_context(self, instance, request, **kwargs):
        return dict(
            options=kwargs,
            request=request,
            template=self,
            nothing=None)

    __get__ = bind

class PageTemplateFile(PageTemplate, chameleon.zpt.template.PageTemplateFile):
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

        chameleon.zpt.template.PageTemplateFile.__init__(
            self, filename, **kwargs)

class BoundPageTemplate(object):
    def __init__(self, render, pt):
        object.__setattr__(self, 'im_func', render)
        object.__setattr__(self, 'im_self', pt)

    macros = property(lambda self: self.im_self.macros)
    filename = property(lambda self: self.im_self.filename)

    def __call__(self, *args, **kw):
        return self.im_func(*args, **kw)

    def __setattr__(self, name, v):
        raise AttributeError("Can't set attribute", name)

    def __repr__(self):
        return "<%s.Bound%s %r>" % (
            type(self.im_self).__module__,
            type(self.im_self).__name__, self.filename)

class ViewPageTemplate(PageTemplate):
    """Template class suitable for use with a Zope browser view; the
    variables ``view``, ``context`` and ``request`` variables are
    brought in to the local scope of the template automatically, while
    keyword arguments are passed in through the ``options``
    dictionary. Note that the default expression type for this class
    is 'path' (standard Zope traversal)."""

    def _pt_get_context(self, view, request, **kwargs):
        return dict(
            view=view,
            context=view.context,
            request=request or view.request,
            template=self,
            options=kwargs,
            nothing=None)

class ViewPageTemplateFile(ViewPageTemplate, PageTemplateFile):
    """If ``filename`` is a relative path, the module path of the
    class where the instance is used to get an absolute path."""

