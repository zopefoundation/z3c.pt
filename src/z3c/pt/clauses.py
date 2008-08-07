# -*- coding: utf-8 -*-

from cgi import escape

from z3c.pt import types
from z3c.pt.utils import unicode_required_flag

class Assign(object):
    """
    >>> from z3c.pt.generation import CodeIO; stream = CodeIO()
    >>> from z3c.pt.testing import pyexp

    We'll define some values for use in the tests.
    
    >>> one = types.value("1")
    >>> bad_float = types.value("float('abc')")
    >>> abc = types.value("'abc'")
    >>> ghi = types.value("'ghi'")
    >>> utf8_encoded = types.value("'La Peña'")
    >>> exclamation = types.value("'!'")
        
    Simple value assignment:
    
    >>> assign = Assign(one)
    >>> assign.begin(stream, 'a')
    >>> exec stream.getvalue()
    >>> a == 1
    True
    >>> assign.end(stream)
    
    Try-except parts (bad, good):
    
    >>> assign = Assign(types.parts((bad_float, one)))
    >>> assign.begin(stream, 'b')
    >>> exec stream.getvalue()
    >>> b == 1
    True
    >>> assign.end(stream)
    
    Try-except parts (good, bad):
    
    >>> assign = Assign(types.parts((one, bad_float)))
    >>> assign.begin(stream, 'b')
    >>> exec stream.getvalue()
    >>> b == 1
    True
    >>> assign.end(stream)
    
    Join:

    >>> assign = Assign(types.join((abc, ghi)))
    >>> assign.begin(stream, 'b')
    >>> exec stream.getvalue()
    >>> b == 'abcghi'
    True
    >>> assign.end(stream)

    Join with try-except parts:
    
    >>> assign = Assign(types.join((types.parts((bad_float, abc, ghi)), ghi)))
    >>> assign.begin(stream, 'b')
    >>> exec stream.getvalue()
    >>> b == 'abcghi'
    True
    >>> assign.end(stream)

    UTF-8 coercing:

    >>> assign = Assign(types.join((utf8_encoded, exclamation)))
    >>> assign.begin(stream, 'b')
    >>> exec stream.getvalue()
    >>> b == 'La Peña!'
    True
    >>> assign.end(stream)

    UTF-8 coercing with unicode:
    
    >>> assign = Assign(types.join((utf8_encoded, u"!")))
    >>> assign.begin(stream, 'b')
    >>> exec stream.getvalue()
    >>> b == 'La Peña!'
    True
    >>> assign.end(stream)

    """

    def __init__(self, parts, variable=None):
        if not isinstance(parts, types.parts):
            parts = types.parts((parts,))
        
        self.parts = parts
        self.variable = variable
        
    def begin(self, stream, variable=None):
        """First n - 1 expressions must be try-except wrapped."""

        variable = variable or self.variable

        for value in self.parts[:-1]:
            stream.write("try:")
            stream.indent()

            self._assign(variable, value, stream)
            
            stream.outdent()
            stream.write("except Exception, e:")
            stream.indent()

        value = self.parts[-1]
        self._assign(variable, value, stream)
        
        stream.outdent(len(self.parts)-1)

    def _assign(self, variable, value, stream):
        stream.annotate(value)
        
        if isinstance(value, types.value):
            stream.write("%s = %s" % (variable, value))
        elif isinstance(value, types.join):
            parts = []
            _v_count = 0
            
            for part in value:
                if isinstance(part, (types.parts, types.join)):
                    _v = stream.save()
                    assign = Assign(part, _v)
                    assign.begin(stream)
                    assign.end(stream)
                    _v_count +=1
                    parts.append(_v)
                elif isinstance(part, types.value):
                    parts.append(part)
                elif isinstance(part, unicode):
                    parts.append(repr(part.encode('utf-8')))
                elif isinstance(part, str):
                    parts.append(repr(part))
                else:
                    raise ValueError("Not able to handle %s" % type(part))
                    
            format = "%s"*len(parts)

            stream.write("%s = '%s' %% (%s)" % (variable, format, ",".join(parts)))
            
            for i in range(_v_count):
                stream.restore()
        
    def end(self, stream):
        pass

class Define(object):
    """
      >>> from z3c.pt.generation import CodeIO; stream = CodeIO()
      >>> from z3c.pt.testing import pyexp
      
    Variable scope:

      >>> define = Define("a", pyexp("b"))
      >>> b = object()
      >>> define.begin(stream)
      >>> exec stream.getvalue()
      >>> a is b
      True
      >>> del a
      >>> define.end(stream)
      >>> exec stream.getvalue()
      >>> a
      Traceback (most recent call last):
          ...
      NameError: name 'a' is not defined
      >>> b is not None
      True

    Multiple defines:

      >>> stream = CodeIO()
      >>> define1 = Define("a", pyexp("b"))
      >>> define2 = Define("c", pyexp("d"))
      >>> d = object()
      >>> define1.begin(stream)
      >>> define2.begin(stream)
      >>> exec stream.getvalue()
      >>> a is b and c is d
      True
      >>> define2.end(stream)
      >>> define1.end(stream)
      >>> del a; del c
      >>> stream.scope[-1].remove('a'); stream.scope[-1].remove('c')
      >>> exec stream.getvalue()
      >>> a
      Traceback (most recent call last):
          ...
      NameError: name 'a' is not defined
      >>> c
      Traceback (most recent call last):
          ...
      NameError: name 'c' is not defined
      >>> b is not None and d is not None
      True

    Tuple assignments:

      >>> stream = CodeIO()
      >>> define = Define(['e', 'f'], pyexp("[1, 2]"))
      >>> define.begin(stream)
      >>> exec stream.getvalue()
      >>> e == 1 and f == 2
      True
      >>> define.end(stream)

    Verify scope is preserved on tuple assignment:

      >>> stream = CodeIO()
      >>> e = None; f = None
      >>> stream.scope[-1].add('e'); stream.scope[-1].add('f')
      >>> stream.scope.append(set())
      >>> define.begin(stream)
      >>> define.end(stream)
      >>> exec stream.getvalue()
      >>> e is None and f is None
      True

    Using semicolons in expressions within a define:

      >>> stream = CodeIO()
      >>> define = Define("a", pyexp("';'"))
      >>> define.begin(stream)
      >>> exec stream.getvalue()
      >>> a
      ';'
      >>> define.end(stream)

    Scope:

      >>> stream = CodeIO()
      >>> a = 1
      >>> stream.scope[-1].add('a')
      >>> stream.scope.append(set())
      >>> define = Define("a", pyexp("2"))
      >>> define.begin(stream)
      >>> define.end(stream)
      >>> exec stream.getvalue()
      >>> a
      1
    
    """
    def __init__(self, definition, expression):
        if not isinstance(definition, (list, tuple)):
            definition = (definition,)

        if len(definition) == 1:
            variable = definition[0]
        else:
            variable = u"(%s,)" % ", ".join(definition)

        self.assign = Assign(expression, variable)        
        self.definitions = definition
        
    def begin(self, stream):
        # save local variables already in in scope
        for var in self.definitions:
            temp = stream.save()

            # If we didn't set the variable in this scope already
            if var not in stream.scope[-1]:

                # we'll check if it's set in one of the older scopes
                for scope in stream.scope[:-1]:
                    if var in scope:
                        # in which case we back it up
                        stream.write('%s = %s' % (temp, var))

                stream.scope[-1].add(var)
                   
        self.assign.begin(stream)

    def end(self, stream):
        self.assign.end(stream)

        # back come the variables that were already in scope in the
        # first place
        for var in reversed(self.definitions):
            temp = stream.restore()

            # If we set the variable in this scope already
            if var in stream.scope[-1]:

                # we'll check if it's set in one of the older scopes
                for scope in stream.scope[:-1]:
                    if var in scope:
                        # in which case we restore it
                        stream.write('%s = %s' % (var, temp))
                        stream.scope[-1].remove(var)
                        break
                else:
                    stream.write("del %s" % var)

class Condition(object):
    """
      >>> from z3c.pt.generation import CodeIO
      >>> from z3c.pt.testing import pyexp
      >>> from StringIO import StringIO
      
    Unlimited scope:
    
      >>> stream = CodeIO()
      >>> true = Condition(pyexp("True"))
      >>> false = Condition(pyexp("False"))
      >>> true.begin(stream)
      >>> stream.write("print 'Hello'")
      >>> true.end(stream)
      >>> false.begin(stream)
      >>> stream.write("print 'Universe!'")
      >>> false.end(stream)
      >>> stream.write("print 'World!'")
      >>> exec stream.getvalue()
      Hello
      World!

    Finalized limited scope:

      >>> _out = StringIO(); _write = _out.write; stream = CodeIO()
      >>> true = Condition(pyexp("True"), [Write(pyexp("'Hello'"))])
      >>> false = Condition(pyexp("False"), [Write(pyexp("'Hallo'"))])
      >>> true.begin(stream)
      >>> true.end(stream)
      >>> false.begin(stream)
      >>> false.end(stream)
      >>> exec stream.getvalue()
      >>> _out.getvalue()
      'Hello'

    Open limited scope:

      >>> _out = StringIO(); _write = _out.write; stream = CodeIO()
      >>> true = Condition(pyexp("True"), [Tag('div')], finalize=False)
      >>> false = Condition(pyexp("False"), [Tag('span')], finalize=False)
      >>> true.begin(stream)
      >>> stream.out("Hello World!")
      >>> true.end(stream)
      >>> false.begin(stream)
      >>> false.end(stream)
      >>> exec stream.getvalue()
      >>> _out.getvalue()
      '<div>Hello World!</div>'
          
    """
      
    def __init__(self, value, clauses=None, finalize=True):
        self.assign = Assign(value)
        self.clauses = clauses
        self.finalize = finalize
        
    def begin(self, stream):
        temp = stream.save()
        self.assign.begin(stream, temp)
        stream.write("if %s:" % temp)
        stream.indent()
        if self.clauses:
            for clause in self.clauses:
                clause.begin(stream)
            if self.finalize:
                for clause in reversed(self.clauses):
                    clause.end(stream)
            stream.outdent()
        
    def end(self, stream):
        temp = stream.restore()

        if self.clauses:
            if not self.finalize:
                stream.write("if %s:" % temp)
                stream.indent()
                for clause in reversed(self.clauses):
                    clause.end(stream)
                    stream.outdent()
        else:
            stream.outdent()
        self.assign.end(stream)

class Else(object):
    def __init__(self, clauses=None):
        self.clauses = clauses
        
    def begin(self, stream):
        stream.write("else:")
        stream.indent()
        if self.clauses:
            for clause in self.clauses:
                clause.begin(stream)
            for clause in reversed(self.clauses):
                clause.end(stream)
            stream.outdent()
        
    def end(self, stream):
        if not self.clauses:
            stream.outdent()

class Group(object):
    def __init__(self, clauses):
        self.clauses = clauses
        
    def begin(self, stream):
        for clause in self.clauses:
            clause.begin(stream)
        for clause in reversed(self.clauses):
            clause.end(stream)

    def end(self, stream):
        pass

class Visit(object):
    def __init__(self, element):
        self.element = element
        
    def begin(self, stream):
        self.element.visit(skip_macro=False)

    def end(self, stream):
        pass

class Tag(object):
    """
      >>> from z3c.pt.generation import CodeIO
      >>> from z3c.pt.testing import pyexp
      >>> from StringIO import StringIO

      Dynamic attribute:
      
      >>> _out = StringIO(); _write = _out.write; stream = CodeIO()
      >>> tag = Tag('div', dict(alt=pyexp(repr('Hello World!'))))
      >>> tag.begin(stream)
      >>> stream.out('Hello Universe!')
      >>> tag.end(stream)
      >>> exec stream.getvalue()
      >>> _out.getvalue()
      '<div alt="Hello World!">Hello Universe!</div>'

      Self-closing tag:
      
      >>> _out = StringIO(); _write = _out.write; stream = CodeIO()
      >>> tag = Tag('br', {}, True)
      >>> tag.begin(stream)
      >>> tag.end(stream)
      >>> exec stream.getvalue()
      >>> _out.getvalue()
      '<br />'

      Unicode:
      
      >>> _out = StringIO(); _write = _out.write; stream = CodeIO()
      >>> tag = Tag('div', dict(alt=pyexp(repr('La Peña'))))
      >>> tag.begin(stream)
      >>> stream.out('Hello Universe!')
      >>> tag.end(stream)
      >>> exec stream.getvalue()
      >>> _out.getvalue() == '<div alt="La Peña">Hello Universe!</div>'
      True
            
    """

    def __init__(self, tag, attributes={}, selfclosing=False, expression=None):
        i = tag.find('}')

        if i != -1:
            self.tag = tag[i+1:]
        else:
            self.tag = tag

        self.selfclosing = selfclosing
        self.attributes = attributes
        self.expression = expression
        
    def begin(self, stream):
        stream.out('<%s' % self.tag)

        static = filter(
            lambda (attribute, value): \
            not isinstance(value, types.expression),
            self.attributes.items())

        dynamic = filter(
            lambda (attribute, value): \
            isinstance(value, types.expression),
            self.attributes.items())

        for attribute, expression in static:
            stream.out(' %s="%s"' %
               (attribute,
                escape(expression, '"')))

        temp = stream.save()
        temp2 = stream.save()

        if self.expression:
            stream.write("for %s, %s in (%s).items():" % (temp, temp2, self.expression))
            stream.indent()
            if unicode_required_flag:
                stream.write("if isinstance(%s, unicode):" % temp2)
                stream.indent()
                stream.escape(temp2)
                stream.write("_write(' %%s=\"%%s\"' %% (%s, %s))" % (temp, temp2))
                stream.outdent()
                stream.write("elif %s is not None:" % temp2)
            else:
                stream.write("if %s is not None:" % temp2)
            stream.indent()
            stream.write("%s = str(%s)" % (temp2, temp2))
            stream.escape(temp2)
            stream.write("_write(' %%s=\"%%s\"' %% (%s, %s))" % (temp, temp2))
            stream.outdent()
        
        for attribute, value in dynamic:
            assign = Assign(value)
            assign.begin(stream, temp)
            
            if unicode_required_flag:
                stream.write("if isinstance(%s, unicode):" % temp)
                stream.indent()
                stream.write("_write(' %s=\"')" % attribute)
                stream.write("_esc = %s" % temp)
                stream.escape("_esc")
                stream.write("_write(_esc)")
                stream.write("_write('\"')")
                stream.outdent()
                stream.write("elif %s is not None:" % temp)
            else:
                stream.write("if %s is not None:" % temp)
            stream.indent()
            stream.write("_write(' %s=\"')" % attribute)
            stream.write("_esc = str(%s)" % temp)
            stream.escape("_esc")
            stream.write("_write(_esc)")
            stream.write("_write('\"')")
            stream.outdent()
            assign.end(stream)

        stream.restore()
        stream.restore()
        
        if self.selfclosing:
            stream.out(" />")
        else:
            stream.out(">")

    def end(self, stream):
        if not self.selfclosing:
            stream.out('</%s>' % self.tag)

class Repeat(object):
    """
      >>> from z3c.pt.generation import CodeIO
      >>> from z3c.pt.testing import pyexp

    We need to set up the repeat object.

      >>> from z3c.pt import utils
      >>> repeat = utils.repeatdict()

    Simple repeat loop and repeat data structure:

      >>> stream = CodeIO()
      >>> _repeat = Repeat("i", pyexp("range(5)"))
      >>> _repeat.begin(stream)
      >>> stream.write("r = repeat['i']")
      >>> stream.write("print (i, r.index, r.start, r.end, r.number(), r.odd(), r.even())")
      >>> _repeat.end(stream)
      >>> exec stream.getvalue()
      (0, 0, True, False, 1, False, True)
      (1, 1, False, False, 2, True, False)
      (2, 2, False, False, 3, False, True)
      (3, 3, False, False, 4, True, False)
      (4, 4, False, True, 5, False, True)
      >>> _repeat.end(stream)

    A repeat over an empty set.

      >>> stream = CodeIO()
      >>> _repeat = Repeat("j", pyexp("range(0)"))
      >>> _repeat.begin(stream)
      >>> _repeat.end(stream)
      >>> exec stream.getvalue()

    Simple for loop:

      >>> stream = CodeIO()
      >>> _for = Repeat("i", pyexp("range(3)"), repeatdict=False)
      >>> _for.begin(stream)
      >>> stream.write("print i")
      >>> _for.end(stream)
      >>> exec stream.getvalue()
      0
      1
      2
      >>> _for.end(stream)

    """

    def __init__(self, v, e, scope=(), repeatdict=True):
        self.variable = v
        self.expression = e
        self.define = Define(v, types.value("None"))
        self.assign = Assign(e)
        self.repeatdict = repeatdict

    def begin(self, stream):
        variable = self.variable

        if self.repeatdict:
            iterator = stream.save()

            # assign iterator
            self.assign.begin(stream, iterator)

            # initialize variable scope
            self.define.begin(stream)

            # initialize iterator
            stream.write("%s = repeat.insert('%s', %s)" % (
                iterator, variable, iterator))

            # loop
            stream.write("try:")
            stream.indent()
            stream.write("while True:")
            stream.indent()
            stream.write("%s = %s.next()" % (variable, iterator))
        else:
            stream.write("for %s in %s:" % (variable, self.expression))
            stream.indent()

    def end(self, stream):
        # cook before leaving loop
        stream.cook()
        stream.outdent()

        if self.repeatdict:
            stream.outdent()
            stream.write("except StopIteration:")
            stream.indent()
            stream.write("pass")
            stream.outdent()

            self.define.end(stream)
            self.assign.end(stream)
            stream.restore()

class Write(object):
    """
    >>> from z3c.pt.generation import CodeIO
    >>> from z3c.pt.testing import pyexp
    >>> from StringIO import StringIO

    Basic write:
    
    >>> _out = StringIO(); _write = _out.write; stream = CodeIO()
    >>> write = Write(pyexp("'New York'"))
    >>> write.begin(stream)
    >>> write.end(stream)
    >>> exec stream.getvalue()
    >>> _out.getvalue()
    'New York'

    Try-except parts:

    >>> _out = StringIO(); _write = _out.write; stream = CodeIO()
    >>> write = Write(pyexp("undefined | 'New Delhi'"))
    >>> write.begin(stream)
    >>> write.end(stream)
    >>> exec stream.getvalue()
    >>> _out.getvalue()
    'New Delhi'

    Unicode:

    >>> _out = StringIO(); _write = _out.write; stream = CodeIO()
    >>> write = Write(types.value("unicode('La Pe\xc3\xb1a', 'utf-8')"))
    >>> write.begin(stream)
    >>> write.end(stream)
    >>> exec stream.getvalue()
    >>> _out.getvalue() == unicode('La Pe\xc3\xb1a', 'utf-8')
    True
    """

    value = assign = None
    
    def __init__(self, value):
        if isinstance(value, types.parts):
            self.assign = Assign(value)
        else:
            self.value = value

        self.structure = not isinstance(value, types.escape)
        
    def begin(self, stream):
        temp = stream.save()

        if self.value:
            expr = self.value
        else:
            self.assign.begin(stream, temp)
            expr = temp

        stream.write("_urf = %s" % expr)

        stream.write("if _urf is not None:")
        stream.indent()
        if unicode_required_flag:
            stream.write("if not isinstance(_urf, unicode):")
            stream.indent()
            stream.write("_urf = str(_urf)")
            stream.outdent()
        else:
            stream.write("_urf = str(_urf)")
        if self.structure:
            stream.write("_write(_urf)")
        else:
            # Inlined escape function
            stream.write("if '&' in _urf:")
            stream.indent()
            stream.write("_urf = _urf.replace('&', '&amp;')")
            stream.outdent()
            stream.write("if '<' in _urf:")
            stream.indent()
            stream.write("_urf = _urf.replace('<', '&lt;')")
            stream.outdent()
            stream.write("if '>' in _urf:")
            stream.indent()
            stream.write("_urf = _urf.replace('>', '&gt;')")
            stream.outdent()
            stream.write("_write(_urf)")
        stream.outdent()

    def end(self, stream):
        if self.assign:
            self.assign.end(stream)
        stream.restore()

class UnicodeWrite(Write):
    """
    >>> from z3c.pt.generation import CodeIO
    >>> from StringIO import StringIO

    Basic write:

    >>> _out = StringIO(); _write = _out.write; stream = CodeIO()
    >>> write = Write(types.value("'New York'"))
    >>> write.begin(stream)
    >>> write.end(stream)
    >>> exec stream.getvalue()
    >>> _out.getvalue()
    'New York'

    Unicode:

    >>> _out = StringIO(); _write = _out.write; stream = CodeIO()
    >>> write = Write(types.value("unicode('La Pe\xc3\xb1a', 'utf-8')"))
    >>> write.begin(stream)
    >>> write.end(stream)
    >>> exec stream.getvalue()
    >>> _out.getvalue() == unicode('La Pe\xc3\xb1a', 'utf-8')
    True

    Invalid:

    >>> _out = StringIO(); _write = _out.write; stream = CodeIO()
    >>> write = Write(types.value("None"))
    >>> write.begin(stream)
    >>> write.end(stream)
    >>> exec stream.getvalue()
    >>> _out.getvalue()
    ''
    """

    def begin(self, stream):
        temp = stream.save()

        if self.value:
            expr = self.value
        else:
            self.assign.begin(stream, temp)
            expr = temp

        stream.write("_write(%s)" % expr)

class Out(object):
    """
      >>> from z3c.pt.generation import CodeIO
      >>> from z3c.pt.testing import pyexp
      >>> from StringIO import StringIO
      
      >>> _out = StringIO(); _write = _out.write; stream = CodeIO()
      >>> out = Out('Hello World!')
      >>> out.begin(stream)
      >>> out.end(stream)
      >>> exec stream.getvalue()
      >>> _out.getvalue()
      'Hello World!'      
    """
    
    def __init__(self, string, defer=False):
        self.string = string
        self.defer = defer
        
    def begin(self, stream):
        if not self.defer:
            stream.out(self.string)

    def end(self, stream):
        if self.defer:
            stream.out(self.string)

class Translate(object):
    """
    The translate clause works retrospectively.
    """

    def begin(self, stream):
        raise

    def end(self, stream):
        raise

class Method(object):
    """
      >>> from z3c.pt.generation import CodeIO
      >>> from z3c.pt.testing import pyexp
      >>> from StringIO import StringIO
      
      >>> _out = StringIO(); _write = _out.write; stream = CodeIO()
      >>> method = Method('test', ('a', 'b', 'c'))
      >>> method.begin(stream)
      >>> stream.write('print a, b, c')
      >>> method.end(stream)
      >>> exec stream.getvalue()
      >>> test(1, 2, 3)
      1 2 3
      
    """

    def __init__(self, name, args):
        self.name = name
        self.args = args
        
    def begin(self, stream):
        stream.write('def %s(%s):' % (self.name, ", ".join(self.args)))
        stream.indent()

    def end(self, stream):
        stream.outdent()
        
    
