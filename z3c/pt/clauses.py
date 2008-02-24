from expressions import value
from utils import unicode_required_flag

from cgi import escape

class Assign(object):
    """
      >>> from z3c.pt.io import CodeIO; stream = CodeIO()

    Simple assignment:

      >>> assign = Assign(value("1"))
      >>> assign.begin(stream, 'a')
      >>> exec stream.getvalue()
      >>> a == 1
      True
      >>> assign.end(stream)

    Try-except chain:

      >>> assign = Assign(value("float('abc') | 1"))
      >>> assign.begin(stream, 'b')
      >>> exec stream.getvalue()
      >>> b == 1
      True
      >>> assign.end(stream)

    Try-except chain part 2: 

      >>> assign = Assign(value("'abc' | 1"))
      >>> assign.begin(stream, 'b')
      >>> exec stream.getvalue()
      >>> b == 'abc'
      True
      >>> assign.end(stream)
     """
    
    def __init__(self, expressions, variable=None):
        self.expressions = expressions
        self.variable = variable

    def begin(self, stream, variable=None):
        """First n - 1 expressions must be try-except wrapped."""

        variable = variable or self.variable
            
        for expression in self.expressions[:-1]:
            stream.write("try:")
            stream.indent()
            stream.write("%s = %s" % (variable, expression))
            stream.outdent()
            stream.write("except Exception, e:")
            stream.indent()

        expression = self.expressions[-1]
        stream.write("%s = %s" % (variable, expression))

        stream.outdent(len(self.expressions)-1)
        
    def end(self, stream):
        pass
        
class Define(object):
    """
      >>> from z3c.pt.io import CodeIO; stream = CodeIO()

    Variable scope:

      >>> define = Define("a", value("b"))
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
      >>> define1 = Define("a", value("b"))
      >>> define2 = Define("c", value("d"))
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
      >>> define = Define(['e', 'f'], value("[1, 2]"))
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
      >>> define = Define("a", value("';'"))
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
      >>> define = Define("a", value("2"))
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
      >>> from z3c.pt.io import CodeIO

    Unlimited scope:
    
      >>> stream = CodeIO()
      >>> true = Condition(value("True"))
      >>> false = Condition(value("False"))
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

      >>> stream = CodeIO()
      >>> from StringIO import StringIO
      >>> _out = StringIO()
      >>> true = Condition(value("True"), [Write(value("'Hello'"))])
      >>> false = Condition(value("False"), [Write(value("'Hallo'"))])
      >>> true.begin(stream)
      >>> true.end(stream)
      >>> false.begin(stream)
      >>> false.end(stream)
      >>> exec stream.getvalue()
      >>> _out.getvalue()
      'Hello'

    Open limited scope:

      >>> stream = CodeIO()
      >>> from StringIO import StringIO
      >>> _out = StringIO()
      >>> true = Condition(value("True"), [Tag('div')], finalize=False)
      >>> false = Condition(value("False"), [Tag('span')], finalize=False)
      >>> true.begin(stream)
      >>> stream.out("Hello World!")
      >>> true.end(stream)
      >>> false.begin(stream)
      >>> false.end(stream)
      >>> exec stream.getvalue()
      >>> _out.getvalue()
      '<div>Hello World!</div>'
          
    """
      
    def __init__(self, expression, clauses=None, finalize=True):
        self.assign = Assign(expression)
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
    
class Tag(object):
    """
      >>> from z3c.pt.io import CodeIO
      >>> from StringIO import StringIO
      >>> from cgi import escape as _escape
      
      >>> _out = StringIO(); stream = CodeIO()
      >>> tag = Tag('div', dict(alt=value(repr('Hello World!'))))
      >>> tag.begin(stream)
      >>> stream.out('Hello Universe!')
      >>> tag.end(stream)
      >>> exec stream.getvalue()
      >>> _out.getvalue()
      '<div alt="Hello World!">Hello Universe!</div>'

      >>> _out = StringIO(); stream = CodeIO()
      >>> tag = Tag('br', {}, True)
      >>> tag.begin(stream)
      >>> tag.end(stream)
      >>> exec stream.getvalue()
      >>> _out.getvalue()
      '<br />'
      
    """

    def __init__(self, tag, attributes={}, selfclosing=False):
        i = tag.find('}')

        if i != -1:
            self.tag = tag[i+1:]
        else:
            self.tag = tag

        self.selfclosing = selfclosing
        self.attributes = attributes
        
    def begin(self, stream):
        stream.out('<%s' % self.tag)

        # static attributes
        static = filter(
            lambda (attribute, expression): \
            not isinstance(expression, (tuple, list)),
            self.attributes.items())

        dynamic = filter(
            lambda (attribute, expression): \
            isinstance(expression, (tuple, list)),
            self.attributes.items())

        for attribute, expression in static:
            stream.out(' %s="%s"' %
               (attribute,
                escape(expression, '"')))

        temp = stream.save()
        
        for attribute, expression in dynamic:
            assign = Assign(expression)
            assign.begin(stream, temp)
            
            # only include attribute if value is non-trivial
            stream.write("if %s is not None:" % temp)
            stream.indent()

            # if callable, evaluate method
            stream.write("if callable(%s): %s = %s()" % (temp, temp, temp))

            if unicode_required_flag:
                stream.write("if isinstance(%s, unicode):" % temp)
                stream.indent()
                stream.write("%s = %s.encode('utf-8')" % (temp, temp))
                stream.outdent()
                stream.write("else:")
                stream.indent()
                stream.write("%s = str(%s)" % (temp, temp))
                stream.outdent()
            else:
                stream.write("%s = str(%s)" % (temp, temp))
                
            stream.write("_out.write(' %s=\"' + _escape(%s, \"\\\"\"))" %
                         (attribute, temp))
            stream.out('"')
            
            assign.end(stream)
            stream.outdent()

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
      >>> from z3c.pt.io import CodeIO; stream = CodeIO()

    We need to set up the repeat object.

      >>> from z3c.pt import utils
      >>> repeat = utils.repeatdict()

    Simple repeat loop and repeat data structure:

      >>> _repeat = Repeat("i", value("range(5)"))
      >>> _repeat.begin(stream)
      >>> stream.write("r = repeat['i']")
      >>> stream.write("print (i, r.index, r.start, r.end, r.number(), r.odd(), r.even())")
      >>> exec stream.getvalue()
      (0, 0, True, False, 1, False, True)
      (1, 1, False, False, 2, True, False)
      (2, 2, False, False, 3, False, True)
      (3, 3, False, False, 4, True, False)
      (4, 4, False, True, 5, False, True)
      >>> _repeat.end(stream)
      
    """
        
    def __init__(self, v, e, scope=()):
        self.variable = v
        self.define = Define(v, value("None"))
        self.assign = Assign(e)

    def begin(self, stream):
        variable = self.variable
        iterator = stream.save()

        # assign iterator
        self.assign.begin(stream, iterator)

        # initialize variable scope
        self.define.begin(stream)

        # initialize iterator
        stream.write("repeat['%s'] = %s = %s.__iter__()" % (variable, iterator, iterator))

        # loop
        stream.write("while %s:" % iterator)
        stream.indent()
        stream.write("%s = %s.next()" % (variable, iterator))

    def end(self, stream):
        # cook before leaving loop
        stream.cook()
        
        stream.outdent()
        self.define.end(stream)
        self.assign.end(stream)
        stream.restore()

class Write(object):
    """
      >>> from z3c.pt.io import CodeIO; stream = CodeIO()
      >>> from StringIO import StringIO

      >>> _out = StringIO()
      >>> write = Write(value("'New York'"))
      >>> write.begin(stream)
      >>> write.end(stream)
      >>> exec stream.getvalue()
      >>> _out.getvalue()
      'New York'
      >>> _out = StringIO()
      >>> write = Write(value("undefined | ', New York!'"))
      >>> write.begin(stream)
      >>> write.end(stream)
      >>> exec stream.getvalue()
      >>> _out.getvalue()
      'New York, New York!'
    """
    
    def __init__(self, expressions):
        self.assign = Assign(expressions)
        self.expressions = expressions
        self.count = len(expressions)
        
    def begin(self, stream):
        temp = stream.save()

        if self.count == 1:
            expr = self.expressions[0]
        else:
            self.assign.begin(stream, temp)
            expr = temp

        stream.write("_urf = %s" % expr)
        stream.write("if callable(_urf): _urf = _urf()")
        stream.write("if _urf is None: _urf = ''")

        if unicode_required_flag:
            stream.write("if isinstance(_urf, unicode):")
            stream.indent()
            stream.write("_out.write(_urf.encode('utf-8'))")
            stream.outdent()
            stream.write("else:")
            stream.indent()
            stream.write("_out.write(str(_urf))")
            stream.outdent()
        else:
            stream.write("_out.write(str(_urf))")
            
    def end(self, stream):
        if self.count != 1:
            self.assign.end(stream)
        stream.restore()

class Out(object):
    """
      >>> from z3c.pt.io import CodeIO; stream = CodeIO()
      >>> from StringIO import StringIO
      >>> _out = StringIO()
      
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
