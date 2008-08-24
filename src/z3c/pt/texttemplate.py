import pagetemplate
import translation

class TextTemplate(pagetemplate.PageTemplate):
    __doc__ = pagetemplate.PageTemplate.__doc__ # for Sphinx autodoc
    format = 'text'

class TextTemplateFile(pagetemplate.PageTemplateFile):
    __doc__ = pagetemplate.PageTemplateFile.__doc__ # for Sphinx autodoc
    format = 'text'

class ViewTextTemplate(property):
    def __init__(self, body):
        self.template = TextTemplate(body)
        property.__init__(self, self.render)

    def render(self, view):
        def template(**kwargs):
            return self.template.render(view=view,
                                        context=view.context,
                                        request=view.request,
                                        _context=view.request,
                                        options=kwargs)
        return template        
    
class ViewTextTemplateFile(ViewTextTemplate):
    def __init__(self, filename):
        self.template = TextTemplateFile(filename)
        property.__init__(self, self.render)
