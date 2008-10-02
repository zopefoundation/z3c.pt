import os
import sys

from chameleon.zpt.template import PageTemplate
from chameleon.zpt.template import PageTemplateFile
from chameleon.zpt.language import Parser

class ZopePageTemplate(PageTemplate):
    default_parser = Parser(default_expression='path')

class ZopePageTemplateFile(PageTemplateFile):
    default_parser = Parser(default_expression='path')
    
class ViewPageTemplate(property):
    """Template class suitable for use with a Zope browser view; the
    variables ``view``, ``context`` and ``request`` variables are
    brought in to the local scope of the template automatically, while
    keyword arguments are passed in through the ``options``
    dictionary. Note that the default expression type for this class
    is 'path' (standard Zope traversal)."""
    
    template_class = ZopePageTemplate

    def __init__(self, body, **kwargs):
        self.template = self.template_class(body, **kwargs)
        property.__init__(self, self.bind)

    def bind(self, view, request=None, macro=None, global_scope=True):
        def render(**kwargs):
            template = self.template
            
            parameters = dict(
                view=view,
                context=view.context,
                request=request or view.request,
                template=template,
                options=kwargs)

            if macro is None:
                return template.render(**parameters)
            else:
                return template.render_macro(
                    macro, global_scope=global_scope, parameters=parameters)
            
        return render

    @property
    def macros(self):
        return self.template.macros
    
class ViewPageTemplateFile(ViewPageTemplate):
    """If ``filename`` is a relative path, the module path of the
    class where the instance is used to get an absolute path."""

    template_class = ZopePageTemplateFile
    
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

        self.template = self.template_class(filename, **kwargs)
        property.__init__(self, self.bind)

    def __call__(self, view, **kwargs):
        template = self.bind(view)
        return template(**kwargs)
