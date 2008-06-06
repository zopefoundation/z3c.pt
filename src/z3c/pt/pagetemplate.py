import os
import sys

import translation
import template

class PageTemplate(template.BaseTemplate):
    @property
    def translate(self):
        return translation.translate_xml

class PageTemplateFile(template.BaseTemplateFile):
    @property
    def translate(self):
        return translation.translate_xml

class ViewPageTemplate(property):
    def __init__(self, body, **kwargs):
        self.template = PageTemplate(body, **kwargs)
        property.__init__(self, self.render)

    def render(self, view):
        def template(**kwargs):
            return self.template.render(view=view,
                                        context=view.context,
                                        request=view.request,
                                        options=kwargs)
        return template        
    
class ViewPageTemplateFile(ViewPageTemplate):
    def __init__(self, filename, **kwargs):
        self.template = PageTemplateFile(filename, **kwargs)
        property.__init__(self, self.render)
