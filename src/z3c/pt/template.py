import os
import macro
import codegen
import zpt

from z3c.pt.config import DEBUG_MODE
from z3c.pt import filecache
import z3c.pt.generation

class BaseTemplate(object):
    """ Constructs a template object.  Must be passed an input string
    as ``body``. ``default_expression`` is the default expression
    namespace for any ``TALES`` expressions included in the template
    (typically either the string ``path`` or the string ``python``);
    ``python`` is the default if nothing is passed."""

    registry = {}
    cachedir = None
    parser = zpt.ZopePageTemplateParser
    default_expression = 'python'

    def __init__(self, body, parser=None, default_expression=None):
        self.body = body
        self.signature = hash(body)
        self.source = ''

        if default_expression:
            self.default_expression = default_expression

        if parser:
            self.parser = parser
            
    @property
    def translate(self):
        return NotImplementedError("Must be implemented by subclass.")

    @property
    def macros(self):
        return macro.Macros(self.render)

    def cook(self, params, macro=None):
        generator = self.translate(
            self.body, self.parser, macro=macro, params=params,
            default_expression=self.default_expression)
        
        source, _globals = generator()
        suite = codegen.Suite(source, _globals.keys())

        if self.cachedir:
            self.registry.store(params, suite.code)

        self.source = source
        self.selectors = generator.stream.selectors
        self.annotations = generator.stream.annotations
        
        _globals.update(suite._globals)
        return self.execute(suite.code, _globals)

    def cook_check(self, macro, params):
        signature = self.signature, macro, params
        template = self.registry.get(signature, None)
        if template is None:
            template = self.cook(params, macro=macro)
            self.registry[signature] = template
            
        return template
    
    def execute(self, code, _globals):
        _locals = {}
        exec code in _globals, _locals
        return _locals['render']

    def render(self, macro=None, **kwargs):
        template = self.cook_check(macro, tuple(kwargs))
        
        # pass in selectors
        kwargs.update(self.selectors)

        return template(**kwargs)

    def __call__(self, **kwargs):
        return self.render(**kwargs)

    def __repr__(self):
        return u"<%s %d>" % (self.__class__.__name__, id(self))

class BaseTemplateFile(BaseTemplate):
    """ Constructs a template object.  Must be passed an absolute (or
    current-working-directory-relative) filename as ``filename``. If
    ``auto_reload`` is true, each time the template is rendered, it
    will be recompiled if it has been changed since the last
    rendering.  ``cachedir`` is a directory path in which generated
    Python will be stored and cached if non-None.
    ``default_expression`` is the default expression namespace for any
    ``TALES`` expressions included in the template (typically either
    the string ``path`` or the string ``python``); ``python`` is the
    default if nothing is passed."""

    def __init__(self, filename, auto_reload=False, cachedir=None,
                 parser=None, default_expression=None):
        BaseTemplate.__init__(
            self, None, parser=parser, default_expression=default_expression)
        self.auto_reload = auto_reload
        self.cachedir = cachedir

        filename = os.path.abspath(
            os.path.normpath(os.path.expanduser(filename)))

        # make sure file exists
        os.lstat(filename)
        self.filename = filename
        if self.cachedir:
            self.registry = filecache.CachingDict(cachedir, filename,
                                                  self.mtime())
            self.registry.load(self)
        else:
            self.registry = {}

        self.read()
        
    def _get_filename(self):
        return getattr(self, '_filename', None)

    def _set_filename(self, filename):
        self._filename = filename
        self._v_last_read = False

    filename = property(_get_filename, _set_filename)

    def _get_source(self):
        return self._source

    def _set_source(self, source):
        self._source = source

        # write source to disk
        if source and self.filename and DEBUG_MODE:
            filename = "%s.py" % self.filename
            fs = open(filename, 'w')
            fs.write(source)
            fs.close()

    source = property(_get_source, _set_source)

    def read(self):
        fd = open(self.filename, 'r')
        self.body = body = fd.read()
        fd.close()
        self.signature = hash(body)
        self._v_last_read = self.mtime()

    def execute(self, code, _globals=None):
        # TODO: This is evil. We need a better way to get all the globals
        # independent from the generation step
        if _globals is None:
            _globals = codegen.Lookup.globals()
            _globals['generation'] = z3c.pt.generation

        return BaseTemplate.execute(self, code, _globals)

    def cook_check(self, *args):
        if self.auto_reload and self._v_last_read != self.mtime():
            self.read()

        return BaseTemplate.cook_check(self, *args)

    def mtime(self):
        try:
            return os.path.getmtime(self.filename)
        except (IOError, OSError):
            return 0

    def __repr__(self):
        return u"<%s %s>" % (self.__class__.__name__, self.filename)
