from StringIO import StringIO
import lxml.etree

import cgi
import tal
import io

ns_lookup_table = [(f.__ns__, f) for f in \
    (tal.define,
     tal.condition,
     tal.omit,
     tal.repeat,
     tal.attribute,
     tal.replace,
     tal.tag,
     tal.content)]

wrapper = """\
def render(**_kwargs):
\trepeat = _repeatdict()
\t_attrs = {}
\t_scope = _kwargs.keys()
\t_out = _StringIO()
\t_globals = globals()
\tfor _variable, _value in _kwargs.items():
\t\t_globals[_variable] = _value
%s
\treturn _out.getvalue()
"""

def translate(body):
    tree = lxml.etree.parse(StringIO(body))
    root = tree.getroot()

    stream = io.CodeIO(indentation=1, indentation_string="\t")
    visit(root, stream)

    source = wrapper % stream.getvalue()

    _globals = dict(_StringIO=StringIO,
                    _repeatdict=tal.repeatdict,
                    _escape=cgi.escape)

    return source, _globals

def visit(node, stream):
    """Translates a node and outputs to a code stream."""
    
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
            visit(element, stream)

    # end tag
    for handler in reversed(handlers):
        handler.end(stream)

    return stream
