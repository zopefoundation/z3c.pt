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

class ViewPageTemplate(template.BaseViewTemplate):
    def __init__(self, body):
        super(ViewPageTemplate, self).__init__(body)
        self.template = PageTemplate(body)
    
class ViewPageTemplateFile(template.BaseViewTemplateFile):
    def __init__(self, filename):
        super(ViewPageTemplateFile, self).__init__(filename)
        self.template = PageTemplateFile(filename)
