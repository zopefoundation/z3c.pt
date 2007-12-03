import lxml.etree
import StringIO

import tal
import io

ns_lookup_table = [(f.__ns__, f) for f in (tal.define,
                                           tal.condition,
                                           tal.omit,
                                           tal.repeat,
                                           tal.attribute,
                                           tal.replace,
                                           tal.tag,
                                           tal.content)]
                                                 
class PageTemplate(object):
    def __init__(self, body):
        self.body = body
        self.render = None
        
    def translate(self):
        """Translates page template body to Python-code."""

        tree = lxml.etree.parse(StringIO.StringIO(self.body))
        root = tree.getroot()

        stream = io.CodeIO(indentation_string='  ')

        # imports and symbols
        stream.write("from cgi import escape as _escape")
        stream.write("from z3c.pt.tal import repeatdict as _repeatdict")
        stream.write("from StringIO import StringIO as _StringIO")

        stream.write("def render(**_kwargs):")
        stream.indent()
        stream.write("global _StringIO, _repeatdict, _escape")
        stream.write("repeat = _repeatdict()")
        stream.write("_attrs = {}")
        stream.write("_scope = _kwargs.keys()")
        
        # output
        stream.write("_out = _StringIO()")
        
        # set up keyword args
        stream.write("for _variable, _value in _kwargs.items():")
        stream.indent()
        stream.write("globals()[_variable] = _value")
        stream.outdent()

        # translate tree
        translate(root, stream)
        
        # output
        stream.write("return _out.getvalue()")
        stream.outdent()
        
        return stream.getvalue()

    def cook(self):
        exec self.translate()
        self.render = render
        
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

def translate(node, stream):
    keys = node.keys() + [None]
    
    handlers = [handler(node) for key, handler in ns_lookup_table \
                if key in keys]

    # remove namespace attributes
    for key, handler in ns_lookup_table:
        if key is not None and key in node.attrib:
            del node.attrib[key]

    # update node
    for handler in handlers:
        node = handler.update(node)

    # begin tag
    for handler in handlers:
        handler.begin(stream)

    # process children
    if node:
        for element in node:
            translate(element, stream)

    # end tag
    for handler in reversed(handlers):
        handler.end(stream)
