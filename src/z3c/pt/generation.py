from zope.i18n import interpolate
from zope.i18n import translate
from zope.i18nmessageid import Message

import utils
import etree
import expressions

template_wrapper = """\
def render(%(init)s, %(args)s%(extra)s%(language)s=None):
\t%(out)s, %(write)s = %(init)s.initialize_stream()
\t%(attributes)s, %(repeat)s = %(init)s.initialize_tal()
\t%(marker)s = %(init)s.initialize_helpers()
\t%(path)s = %(init)s.initialize_traversal()
\t%(translate)s = %(init)s.fast_translate
\t%(elementtree)s = %(init)s.initialize_elementtree()
\t%(scope)s = {}

%(body)s
\treturn %(out)s.getvalue()
"""

macro_wrapper = """\
def render(%(init)s, %(kwargs)s%(extra)s):
%(body)s
"""

def fast_translate(msgid, domain=None, mapping=None, context=None,
                   target_language=None, default=None):
    """This translation function does not attempt to negotiate a
    language if ``None`` is passed."""
    
    if target_language is not None:
        return translate(
            msgid, domain=domain, mapping=mapping, context=context,
            target_language=target_language, default=default)
    
    if isinstance(msgid, Message):
        default = msgid.default
        mapping = msgid.mapping

    if default is None:
        default = unicode(msgid)

    if not isinstance(default, (str, unicode)):
        return default
    
    return interpolate(default, mapping)

def initialize_tal():
    return ({}, utils.repeatdict())

def initialize_helpers():
    return (object(), )

def initialize_stream():
    out = BufferIO()
    return (out, out.write)

def initialize_traversal():
    return expressions.path_translation.traverse

def initialize_elementtree():
    try:
        return etree.import_elementtree()
    except ImportError:
        return None
    
class BufferIO(list):
    write = list.append

    def getvalue(self):
        return ''.join(self)

class CodeIO(BufferIO):
    """Stream buffer suitable for writing Python-code. This class is
    used internally by the compiler to manage variable scopes, source
    annotations and temporary variables."""

    t_prefix = '_tmp'
    v_prefix = '_var'

    def __init__(self, symbols=None, indentation=0, indentation_string="\t"):
        BufferIO.__init__(self)
        self.symbols = symbols or object
        self.indentation = indentation
        self.indentation_string = indentation_string
        self.queue = ''
        self.scope = [set()]
        self.selectors = {}
        self.annotations = {}
        self._variables = {}
        self.t_counter = 0
        self.l_counter = 0

    def save(self):
        self.t_counter += 1
        return "%s%d" % (self.t_prefix, self.t_counter)

    def restore(self):
        var = "%s%d" % (self.t_prefix, self.t_counter)
        self.t_counter -= 1
        return var

    def indent(self, amount=1):
        if amount > 0:
            self.cook()
            self.indentation += amount

    def outdent(self, amount=1):
        if amount > 0:
            self.cook()
            self.indentation -= amount

    def annotate(self, item):
        self.annotations[self.l_counter] = item

    def out(self, string):
        self.queue += string

    def cook(self):
        if self.queue:
            queue = self.queue
            self.queue = ''
            self.write(
                "%s('%s')" %
                (self.symbols.write, queue.replace('\n', '\\n').replace("'", "\\'")))

    def write(self, string):
        if isinstance(string, unicode):
            string = string.encode('utf-8')

        self.l_counter += len(string.split('\n'))-1

        self.cook()
        BufferIO.write(self,
            self.indentation_string * self.indentation + string + '\n')

    def getvalue(self):
        self.cook()
        return BufferIO.getvalue(self)

    def escape(self, variable):
        self.write("if '&' in %s:" % variable)
        self.indent()
        self.write("%s = %s.replace('&', '&amp;')" % (variable, variable))
        self.outdent()
        self.write("if '<' in %s:" % variable)
        self.indent()
        self.write("%s = %s.replace('<', '&lt;')" % (variable, variable))
        self.outdent()
        self.write("if '>' in %s:" % variable)
        self.indent()
        self.write("%s = %s.replace('>', '&gt;')" % (variable, variable))
        self.outdent()
        self.write("if '\"' in %s:" % variable)
        self.indent()
        self.write("%s = %s.replace('\"', '&quot;')" % (variable, variable))
        self.outdent()
        
    def begin(self, clauses):
        if isinstance(clauses, (list, tuple)):
            for clause in clauses:
                self.begin(clause)
        else:
            clauses.begin(self)
                
    def end(self, clauses):
        if isinstance(clauses, (list, tuple)):
            for clause in reversed(clauses):
                self.end(clause)
        else:
            clauses.end(self)
