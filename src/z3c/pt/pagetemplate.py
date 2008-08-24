import zope.i18n

import translation
import generation
import template
import config
import zpt
import sys
import os

def prepare_language_support(kwargs):
    target_language = kwargs.get('target_language')

    if config.DISABLE_I18N:
        if target_language:
            del kwargs['target_language']
        return
    
    if not target_language:
        context = kwargs.get('context')
        target_language = zope.i18n.negotiate(context)

        if target_language:
            kwargs['target_language'] = target_language    

class PageTemplate(template.BaseTemplate):
    __doc__ = template.BaseTemplate.__doc__ # for Sphinx autodoc

    def __init__(self, body, parser=None):
        if parser is None:
            parser = zpt.ZopePageTemplateParser
        super(PageTemplate, self).__init__(body, parser)

    def prepare(self, kwargs):
        super(PageTemplate, self).prepare(kwargs)
        prepare_language_support(kwargs)

class PageTemplateFile(template.BaseTemplateFile):
    __doc__ = template.BaseTemplateFile.__doc__ # for Sphinx autodoc
    
    def __init__(self, filename, parser=None, **kwargs):
        if parser is None:
            parser = zpt.ZopePageTemplateParser
        super(PageTemplateFile, self).__init__(filename, parser, **kwargs)

    def prepare(self, kwargs):
        super(PageTemplateFile, self).prepare(kwargs)
        prepare_language_support(kwargs)

class ViewPageTemplate(property):
    """Template class suitable for use with a Zope browser view; the
    variables ``view``, ``context`` and ``request`` variables are
    brought in to the local scope of the template automatically, while
    keyword arguments are passed in through the ``options``
    dictionary."""
    
    def __init__(self, body, **kwargs):
        self.template = PageTemplate(body, **kwargs)
        property.__init__(self, self.render)

    def render(self, view):
        def template(**kwargs):
            return self.template.render(view=view,
                                        context=view.context,
                                        request=view.request,
                                        _context=view.request,
                                        options=kwargs)
        return template

class ViewPageTemplateFile(ViewPageTemplate):
    """If ``filename`` is a relative path, the module path of the
    class where the instance is used to get an absolute path."""
    
    def __init__(self, filename, **kwargs):
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
        
        self.template = PageTemplateFile(filename)
        property.__init__(self, self.render)
