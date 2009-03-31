from chameleon.core import config

import chameleon.zpt.language
import pagetemplate

class XHTMLElement(chameleon.zpt.language.XHTMLElement):
    meta_interpolation_escaping = False

class Parser(chameleon.zpt.language.Parser):
    default_expression = "path"

    element_mapping = {
        config.META_NS: {None: XHTMLElement},
        }
    
class TextTemplate(pagetemplate.PageTemplate):
    __doc__ = pagetemplate.PageTemplate.__doc__ # for Sphinx autodoc
    default_parser = Parser()
    format = 'text'

class TextTemplateFile(pagetemplate.PageTemplateFile):
    __doc__ = pagetemplate.PageTemplateFile.__doc__ # for Sphinx autodoc
    default_parser = Parser()
    format = 'text'

class ViewTextTemplate(pagetemplate.ViewPageTemplate):
    __doc__ = pagetemplate.ViewPageTemplate.__doc__ # for Sphinx autodoc
    default_parser = Parser()
    format = 'text'

class ViewTextTemplateFile(pagetemplate.ViewPageTemplateFile):
    __doc__ = pagetemplate.ViewPageTemplateFile.__doc__ # for Sphinx autodoc
    default_parser = Parser()
    format = 'text'
