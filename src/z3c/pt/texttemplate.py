import pagetemplate

class TextTemplate(pagetemplate.PageTemplate):
    __doc__ = pagetemplate.PageTemplate.__doc__ # for Sphinx autodoc
    format = 'text'

class TextTemplateFile(pagetemplate.PageTemplateFile):
    __doc__ = pagetemplate.PageTemplateFile.__doc__ # for Sphinx autodoc
    format = 'text'

class ViewTextTemplate(pagetemplate.ViewPageTemplate):
    __doc__ = pagetemplate.ViewPageTemplate.__doc__ # for Sphinx autodoc
    format = 'text'
    
class ViewTextTemplateFile(pagetemplate.ViewPageTemplateFile):
    __doc__ = pagetemplate.ViewPageTemplateFile.__doc__ # for Sphinx autodoc
    format = 'text'
