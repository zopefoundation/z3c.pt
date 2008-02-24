import template
import translation

class TextTemplate(template.BaseTemplate):
    @property
    def translate(self):
        return translation.translate_text

class TextTemplateFile(template.BaseTemplateFile):
    @property
    def translate(self):
        return translation.translate_text

class ViewTextTemplate(template.BaseViewTemplate):
    def __init__(self, body):
        super(ViewTextTemplate, self).__init__(body)
        self.template = TextTemplate(body)
    
class ViewTextTemplateFile(template.BaseViewTemplateFile):
    def __init__(self, filename):
        super(ViewTextTemplateFile, self).__init__(filename)
        self.template = TextTemplateFile(self.filename)
