import translation
import generation
import expressions
import macro
import etree
import config
import utils

import zpt
import genshi

from StringIO import StringIO

def pyexp(string):
    return expressions.PythonTranslation.expression(string)

def setup_stream():
    class symbols(translation.Element.symbols):
        out = '_out'
        write = '_write'

    out = StringIO()
    write = out.write
    stream = generation.CodeIO(symbols)
    return out, write, stream

def cook(generator, **kwargs):
    source, _globals = generator()
    _locals = {}
    exec source in _globals, _locals
    return _locals['render']

def _render(generator, **kwargs):
    cooked = cook(generator, **kwargs)
    kwargs.update(generator.stream.selectors)
    return cooked(**kwargs)

def render_xhtml(body, **kwargs):
    generator = translation.translate_xml(
        body, MockParser, params=sorted(kwargs.keys()))
    return _render(generator, **kwargs)

def render_text(body, **kwargs):
    generator = translation.translate_text(
        body, MockParser, params=sorted(kwargs.keys()))
    return _render(generator, **kwargs)

def render_zpt(body, **kwargs):
    generator = translation.translate_xml(
        body, zpt.ZopePageTemplateParser, params=sorted(kwargs.keys()))
    return _render(generator, **kwargs)

def render_genshi(body, **kwargs):
    generator = translation.translate_xml(
        body, genshi.GenshiParser, params=sorted(kwargs.keys()))
    return _render(generator, **kwargs)

class MockTemplate(object):
    def __init__(self, body, parser):
        self.body = body
        self.parser = parser

    @property
    def macros(self):
        def render(macro=None, **kwargs):
            generator = translation.translate_xml(
                self.body, self.parser, macro=macro, params=kwargs.keys())
            return _render(generator, **kwargs)
        return macro.Macros(render)

class MockElement(translation.Element, translation.VariableInterpolation):
    translator = expressions.PythonTranslation
    
    def update(self):
        translation.VariableInterpolation.update(self)
        
    class node(object):
        def __init__(self, element):
            self.element = element

        def __getattr__(self, name):
            return None

        @property
        def static_attributes(self):
            return utils.get_attributes_from_namespace(
                self.element, config.XHTML_NS)

        @property
        def omit(self):
            if self.element.meta_omit is not None:
                return self.element.meta_omit or True
            if self.content:
                return True
            
        @property
        def content(self):
            return self.element.meta_replace
        
        @property
        def cdata(self):
            return self.element.meta_cdata

    node = property(node)

class MockParser(etree.Parser):
    element_mapping = {
        config.XHTML_NS: {None: MockElement},
        config.META_NS: {None: MockElement}}
