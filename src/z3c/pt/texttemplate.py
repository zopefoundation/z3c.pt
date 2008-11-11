import pagetemplate

class TextTemplate(pagetemplate.ZopePageTemplate):
    __doc__ = pagetemplate.ZopePageTemplate.__doc__ # for Sphinx autodoc
    format = 'text'

class TextTemplateFile(pagetemplate.ZopePageTemplateFile):
    __doc__ = pagetemplate.ZopePageTemplateFile.__doc__ # for Sphinx autodoc
    format = 'text'

class ViewTextTemplate(pagetemplate.ViewPageTemplate):
    __doc__ = pagetemplate.ViewPageTemplate.__doc__ # for Sphinx autodoc
    template_class = TextTemplate
        
class ViewTextTemplateFile(pagetemplate.ViewPageTemplateFile):
    __doc__ = pagetemplate.ViewPageTemplateFile.__doc__ # for Sphinx autodoc
    template_class = TextTemplateFile
