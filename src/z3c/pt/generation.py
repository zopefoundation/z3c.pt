from zope.i18n import interpolate
from zope.i18n import negotiate
from zope.i18n import translate
from zope.i18nmessageid import Message

import expressions
import utils

import z3c.pt.generation
from z3c.pt.config import DISABLE_I18N

template_wrapper = """\
def render(%(args)s%(extra)s%(language)s=None):
\tglobal %(generation)s

\t%(out)s, %(write)s = generation.initialize_stream()
\t%(attributes)s, %(repeat)s = generation.initialize_tal()
\t%(domain)s, %(negotiate)s, %(translate)s = generation.initialize_i18n()
\t%(marker)s = %(generation)s.initialize_helpers()
\t%(path)s = %(generation)s.initialize_traversal()
\t%(scope)s = {}

\t%(language)s = %(negotiate)s(%(context)s, %(language)s)
%(code)s
\treturn %(out)s.getvalue()
"""

macro_wrapper = """\
def render(%(kwargs)s%(extra)s):
\tglobal %(generation)s
%(code)s
"""

def _fake_negotiate(context, target_language):
    return target_language

def _fake_translate(msgid, domain=None, mapping=None, context=None,
                    target_language=None, default=None):
    if isinstance(msgid, Message):
        default = msgid.default
        mapping = msgid.mapping

    if default is None:
        default = unicode(msgid)

    return interpolate(default, mapping)

def _negotiate(context, target_language):
    if target_language is not None:
        return target_language
    return negotiate(context)

def initialize_i18n():
    if DISABLE_I18N:
        return (None, _fake_negotiate, _fake_translate)
    return (None, _negotiate, translate)

def initialize_tal():
    return ({}, utils.repeatdict())

def initialize_helpers():
    return (object(), )

def initialize_stream():
    out = BufferIO()
    return (out, out.write)

def initialize_traversal():
    return expressions.PathTranslation.traverse

class BufferIO(list):
    write = list.append

    def getvalue(self):
        return ''.join(self)

class CodeIO(BufferIO):
    """A I/O stream class that provides facilities to generate Python code.

    * Indentation is managed using ``indent`` and ``outdent``.

    * Annotations can be assigned on a per-line basis using ``annotate``.

    * Convenience methods for keeping track of temporary variables
   
    * Methods to process clauses (see ``begin`` and ``end``).
    
    """

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
