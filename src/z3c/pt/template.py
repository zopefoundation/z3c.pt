import os
import sys
import codegen
import traceback

from z3c.pt.config import DEBUG_MODE, PROD_MODE

class BaseTemplate(object):
    registry = {}
    default_expression = 'python'
    
    def __init__(self, body, default_expression=None):
        self.body = body
        self.signature = hash(body)
        self.source = ''

        if default_expression:
            self.default_expression = default_expression

    @property
    def translate(self):
        return NotImplementedError("Must be implemented by subclass.")

    def source_write(self):
        # Hook for writing out the source code to the file system
        return

    def cook(self, params):
        generator = self.translate(
            self.body, params=params, default_expression=self.default_expression)
        
        source, _globals = generator()
        
        suite = codegen.Suite(source)

        self.source = source
        self.source_write()
        self.annotations = generator.stream.annotations
        
        _globals.update(suite._globals)
        _locals = {}

        exec suite.code in _globals, _locals

        return _locals['render']

    def render(self, **kwargs):
        # A ''.join of a dict uses only the keys
        signature = self.signature + hash(''.join(kwargs))

        template = self.registry.get(signature, None)
        if template is None:
            self.registry[signature] = template = self.cook(kwargs.keys())

        if PROD_MODE:
            return template(**kwargs)

        return self.safe_render(template, **kwargs)

    def safe_render(self, template, **kwargs):
        try:
            return template(**kwargs)
        except Exception, e:
            __traceback_info__ = getattr(e, '__traceback_info__', None)
            if __traceback_info__ is not None:
                raise e
            
            etype, value, tb = sys.exc_info()
            lineno = tb.tb_next.tb_lineno-1
            annotations = self.annotations

            while lineno >= 0:
                if lineno in annotations:
                    annotation = annotations.get(lineno)
                    break

                lineno -= 1
            else:
                annotation = "n/a"

            e.__traceback_info__ = "While rendering %s, an exception was "\
                                   "raised evaluating ``%s``:\n\n" % \
                                   (repr(self), str(annotation))
            
            e.__traceback_info__ += "".join(traceback.format_tb(tb))
            
            raise e

    def __call__(self, **kwargs):
        return self.render(**kwargs)

    def __repr__(self):
        return u"<%s %d>" % (self.__class__.__name__, id(self))

class BaseTemplateFile(BaseTemplate):
    def __init__(self, filename):
        BaseTemplate.__init__(self, None)

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

    def _get_filename(self):
        return getattr(self, '_filename', None)

    def _set_filename(self, filename):
        self._filename = filename
        self._v_last_read = False

    filename = property(_get_filename, _set_filename)

    @property
    def source_filename(self):
        return "%s.source" % self.filename

    def source_write(self):
        if DEBUG_MODE and self.source_filename:
            fs = open(self.source_filename, 'w')
            fs.write(self.source)
            fs.close()

    def render(self, **kwargs):
        if self._cook_check():
            fd = open(self.filename, 'r')
            self.body = body = fd.read()
            fd.close()
            self.signature = hash(body)
            self._v_last_read = self.mtime()

        return BaseTemplate.render(self, **kwargs)

    def _cook_check(self):
        if self._v_last_read and PROD_MODE:
            return False

        if self.mtime() == self._v_last_read:
            return False

        return True

    def mtime(self):
        try:
            return os.path.getmtime(self.filename)
        except (IOError, OSError):
            return 0

    def __repr__(self):
        return u"<%s %s>" % (self.__class__.__name__, self.filename)
