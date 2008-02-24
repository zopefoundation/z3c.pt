import os
import sys
import codegen

class BaseTemplate(object):
    registry = {}

    def __init__(self, body):
        self.body = body
        self.signature = hash(body)        

    @property
    def translate(self):
        return NotImplementedError("Must be implemented by subclass.")

    def cook(self, params):
        source, _globals = self.translate(self.body, params)
        suite = codegen.Suite(source)

        self.source = source
        
        _globals.update(suite._globals)
        _locals = {}

        exec suite.code in _globals, _locals
        
        return _locals['render']

    def render(self, **kwargs):
        signature = self.signature + hash(",".join(kwargs.keys()))

        template = self.registry.get(signature)
        if not template:
            self.registry[signature] = template = self.cook(kwargs.keys())

        return template(**kwargs)
            
    def __call__(self, **kwargs):
        return self.render(**kwargs)

class BaseTemplateFile(BaseTemplate):
    def __init__(self, filename):
        self.filename = filename
        
    def _get_filename(self):
        return getattr(self, '_filename', None)

    def _set_filename(self, filename):
        self._filename = filename
        self._v_last_read = False

    filename = property(_get_filename, _set_filename)

    def render(self, **kwargs):
        if self._cook_check():
            self.body = open(self.filename, 'r').read()
            self.signature = hash(self.body)
            self._v_last_read = self.mtime()

        return BaseTemplate.render(self, **kwargs)
            
    def _cook_check(self):
        if self._v_last_read and not __debug__:
            return

        if self.mtime() == self._v_last_read:
            return

        return True

    def mtime(self):
        try:
            return os.path.getmtime(self.filename)
        except OSError:
            return 0

class BaseViewTemplate(property):
    def __init__(self, body):
        property.__init__(self, self.render)

    def render(self, view):
        def template(**kwargs):
            return self.template.render(view=view,
                                        context=view.context,
                                        request=view.request,
                                        options=kwargs)
        return template

class BaseViewTemplateFile(BaseViewTemplate):
    def __init__(self, filename):
        if not os.path.isabs(filename):
            package_name = sys._getframe(2).f_globals['__name__']
            module = sys.modules[package_name]
            try:
                path = module.__path__[0]
            except AttributeError:
                path = module.__file__
                path = path[:path.rfind(os.sep)]
                
            filename = path + os.sep + filename

        # make sure file exists
        os.lstat(filename)
        self.filename = filename
        
        property.__init__(self, self.render)
