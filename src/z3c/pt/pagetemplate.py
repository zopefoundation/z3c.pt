import zope.i18n

import translation
import generation
import template
import config
import zpt

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
    def __init__(self, filename, **kwargs):
        self.template = PageTemplateFile(filename)
        property.__init__(self, self.render)
