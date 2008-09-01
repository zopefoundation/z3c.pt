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
    return expressions.python_translation.expression(string)

def setup_stream():
    class symbols(translation.Node.symbols):
        out = '_out'
        write = '_write'

    out = StringIO()
    write = out.write
    stream = generation.CodeIO(symbols)
    return out, write, stream

def render_xhtml(body, **kwargs):
    compiler = translation.Compiler(body, mock_parser)
    template = compiler(params=sorted(kwargs.keys()))
    return template.render(**kwargs)    
    
def render_text(body, **kwargs):
    compiler = translation.Compiler.from_text(body, mock_parser)
    template = compiler(params=sorted(kwargs.keys()))
    return template.render(**kwargs)    

def render_zpt(body, **kwargs):
    compiler = translation.Compiler(body, zpt.ZopePageTemplateParser())
    template = compiler(params=sorted(kwargs.keys()))
    return template.render(**kwargs)    

def render_genshi(body, **kwargs):
    compiler = translation.Compiler(body, genshi.GenshiParser())
    template = compiler(params=sorted(kwargs.keys()))
    kwargs.update(template.selectors)
    return template.render(**kwargs)    

class MockTemplate(object):
    def __init__(self, body, parser):
        self.body = body
        self.parser = parser

    @property
    def macros(self):
        def render(macro=None, **kwargs):
            compiler = translation.Compiler(self.body, self.parser)
            template = compiler(macro=macro, params=kwargs.keys())
            return template.render(**kwargs)
        return macro.Macros(render)

class MockElement(translation.Element, translation.VariableInterpolation):
    translator = expressions.python_translation
    
    def update(self):
        translation.VariableInterpolation.update(self)
        
    class node(translation.Node):
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
            if self.include:
                return True

        @property
        def content(self):
            return self.element.meta_replace
        
        @property
        def cdata(self):
            return self.element.meta_cdata

        @property
        def include(self):
            return self.element.xi_href

        @property
        def format(self):
            return self.element.xi_parse

    node = property(node)

    xi_href = utils.attribute(
        "href", lambda p: expressions.StringTranslation(p).expression)
    xi_parse = utils.attribute("parse", default="xml")

class MockParser(etree.Parser):
    element_mapping = {
        config.XHTML_NS: {None: MockElement},
        config.META_NS: {None: MockElement},
        config.XI_NS: {None: MockElement}}

mock_parser = MockParser()
