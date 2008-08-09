import expressions
import macro

def pyexp(string):
    return expressions.PythonTranslation.expression(string)

def cook(generator, **kwargs):
    source, _globals = generator()
    _locals = {}
    exec source in _globals, _locals
    return _locals['render']

def render(body, translator, **kwargs):
    generator = translator(body, params=sorted(kwargs.keys()))
    return _render(generator, **kwargs)

def _render(generator, **kwargs):
    cooked = cook(generator, **kwargs)
    kwargs.update(generator.stream.selectors)
    return cooked(**kwargs)

class MockTemplate(object):
    def __init__(self, body, translator):
        self.body = body
        self.translator = translator

    @property
    def macros(self):
        def render(macro=None, **kwargs):
            generator = self.translator(
                self.body, macro=macro, params=kwargs.keys())
            return _render(generator, **kwargs)
        return macro.Macros(render)
