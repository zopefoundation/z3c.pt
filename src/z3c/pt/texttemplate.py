import chameleon.zpt.language

import pagetemplate

class TextTemplate(pagetemplate.PageTemplate):
    __doc__ = pagetemplate.PageTemplate.__doc__ # for Sphinx autodoc
    default_parser = chameleon.zpt.language.Parser(default_expression="path")
    format = 'text'

class TextTemplateFile(pagetemplate.PageTemplateFile):
    __doc__ = pagetemplate.PageTemplateFile.__doc__ # for Sphinx autodoc
    default_parser = chameleon.zpt.language.Parser(default_expression="path")
    format = 'text'

class ViewTextTemplate(pagetemplate.ViewPageTemplate):
    __doc__ = pagetemplate.ViewPageTemplate.__doc__ # for Sphinx autodoc
    default_parser = chameleon.zpt.language.Parser(default_expression="path")
    format = 'text'

class ViewTextTemplateFile(pagetemplate.ViewPageTemplateFile):
    __doc__ = pagetemplate.ViewPageTemplateFile.__doc__ # for Sphinx autodoc
    default_parser = chameleon.zpt.language.Parser(default_expression="path")
    format = 'text'
