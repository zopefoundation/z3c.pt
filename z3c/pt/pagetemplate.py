import translation
import codegen
import io

class PageTemplate(object):
    def __init__(self, body):
        self.body = body
        self.init()
        
    def init(self):
        self.registry = {}
        
    def cook(self, params):
        source, _globals = translation.translate(self.body, params)
        suite = codegen.Suite(source)

        _locals = {}

        exec suite.code in _globals, _locals
        
        return _locals['render']

    def render(self, **kwargs):
        signature = hash(",".join(kwargs.keys()))

        template = self.registry.get(signature)
        if not template:
            self.registry[signature] = template = self.cook(kwargs.keys())

        return template(**kwargs)
            
    def __call__(self, **kwargs):
        return self.render(**kwargs)

class PageTemplateFile(PageTemplate):
    def __init__(self, filename):
        self.filename = filename

    def get_filename(self):
        return getattr(self, '_filename', None)

    def set_filename(self, filename):
        self._filename = filename
        self.init()

    filename = property(get_filename, set_filename)
        
    @property
    def body(self):
        return open(self.filename, 'r').read()

class ViewPageTemplateFile(property):
    def __init__(self, filename):
        self.template = PageTemplateFile(filename)

        def render(view):
            def render(**kwargs):
                return self.template.render(view=view,
                                            context=view.context,
                                            request=view.request,
                                            options=kwargs)
            return render
        
        property.__init__(self, render)
