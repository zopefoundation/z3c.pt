import translation
import codegen
                                                 
class PageTemplate(object):
    def __init__(self, body):
        self.body = body
        self.render = None
        
    def cook(self):
        source, _globals = translation.translate(self.body)
        suite = codegen.Suite(source)

        _locals = {}

        exec suite.code in _globals, _locals

        self.render = _locals['render']

    @property
    def template(self):
        if self.render is None:
            self.cook()

        return self.render
        
    def __call__(self, **kwargs):
        return self.template(**kwargs)

class PageTemplateFile(PageTemplate):
    def __init__(self, filename):
        self.filename = filename
        self.render = None

    @property
    def body(self):
        return open(self.filename, 'r').read()
