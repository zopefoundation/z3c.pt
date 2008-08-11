import template
import translation

class TextTemplate(template.BaseTemplate):
    __doc__ = template.BaseTemplate.__doc__ # for Sphinx autodoc
    @property
    def translate(self):
        return translation.translate_text

class TextTemplateFile(template.BaseTemplateFile):
    __doc__ = template.BaseTemplateFile.__doc__ # for Sphinx autodoc
    @property
    def translate(self):
        return translation.translate_text

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
