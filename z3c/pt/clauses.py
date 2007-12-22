from attributes import expression
import utils

class Assign(object):
    """
      >>> from z3c.pt.io import CodeIO; stream = CodeIO()
      >>> _scope = []

    Simple assignment:

      >>> assign = Assign(expression("1"))
      >>> assign.begin(stream, 'a')
      >>> exec stream.getvalue()
      >>> a == 1
      True
      >>> assign.end(stream)

    Try-except chain:

      >>> assign = Assign(expression("float('abc') | 1"))
      >>> assign.begin(stream, 'b')
      >>> exec stream.getvalue()
      >>> b == 1
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
      >>> _scope = []

    Variable scope:

      >>> define = Define("a", expression("b"))
      >>> b = object()
      >>> define.begin(stream)
      >>> exec stream.getvalue()
      >>> a is b
      True
      >>> del a
      >>> _scope.remove('a')
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
      >>> define1 = Define("a", expression("b"))
      >>> define2 = Define("c", expression("d"))
      >>> d = object()
      >>> define1.begin(stream)
      >>> define2.begin(stream)
      >>> exec stream.getvalue()
      >>> a is b and c is d
      True
      >>> define2.end(stream)
      >>> define1.end(stream)
      >>> del a; del c
      >>> _scope.remove('a'); _scope.remove('c')
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
      >>> define = Define("(e, f)", expression("[1, 2]"))
      >>> define.begin(stream)
      >>> exec stream.getvalue()
      >>> e == 1 and f == 2
      True
      >>> define.end(stream)

    Verify scope is preserved on tuple assignment:

      >>> e = None; f = None
      >>> _scope.append('e'); _scope.append('f')
      >>> exec stream.getvalue()
      >>> e is None and f is None
      True

    Using semicolons in expressions within a define:

      >>> stream = CodeIO()
      >>> define = Define("a", expression("';'"))
      >>> define.begin(stream)
      >>> exec stream.getvalue()
      >>> a
      ';'
      >>> define.end(stream)

    Scope:

      >>> stream = CodeIO()
      >>> a = 1
      >>> _scope.append('a')
      >>> define = Define("a", expression("2"))
      >>> define.begin(stream)
      >>> define.end(stream)
      >>> exec stream.getvalue()
      >>> a
      1
    
    """
    def __init__(self, definition, expression, scope=()):
        if not isinstance(definition, (list, tuple)):
            definition = (definition,)

        if len(definition) == 1:
            variable = definition[0]
        else:
            variable = u"(%s,)" % ", ".join(definition)

        self.assign = Assign(expression, variable)

        # only register definitions for variables that have not
        # been defined in this scope
        self.definitions = [var for var in definition if var not in scope]
            
        if scope:
            scope.extend(self.definitions)
        if not scope:
            scope = utils.scope()

        self.scope = scope
        
    def begin(self, stream):
        temp = stream.savevariable(self.scope, '{}')

        # save local variables already in in scope
        for var in self.definitions:
            stream.write("if '%s' in _scope: %s['%s'] = %s" % (var, temp, var, var))
            stream.write("else: _scope.append('%s')" % var)
            
        self.assign.begin(stream)

    def end(self, stream):
        temp = stream.restorevariable(self.scope)

        self.assign.end(stream)
        
        for var in reversed(self.definitions):
            stream.write("if '%s' in %s:" % (var, temp))
            stream.indent()
            stream.write("%s = %s['%s']" % (var, temp, var))
            stream.outdent()
            stream.write("else:")
            stream.indent()
            stream.write("del %s" % var)
            stream.write("_scope.remove('%s')" % var)
            stream.outdent()
            
class Condition(object):
    """
      >>> from z3c.pt.io import CodeIO

    Unlimited scope:
    
      >>> stream = CodeIO()
      >>> true = Condition(expression("True"))
      >>> false = Condition(expression("False"))
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

    Limited scope:

      >>> stream = CodeIO()
      >>> from StringIO import StringIO
      >>> _out = StringIO()
      >>> true = Condition(expression("True"), [Write(expression("'Hello'"))])
      >>> false = Condition(expression("False"), [Write(expression("'Hallo'"))])
      >>> true.begin(stream)
      >>> true.end(stream)
      >>> false.begin(stream)
      >>> false.end(stream)
      >>> exec stream.getvalue()
      >>> _out.getvalue()
      'Hello'
    """
      
    def __init__(self, expression, clauses=None):
        self.assign = Assign(expression)
        self.clauses = clauses
        
    def begin(self, stream):
        temp = stream.save()
        self.assign.begin(stream, temp)
        stream.write("if %s:" % temp)
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
        self.assign.end(stream)
        stream.restore()

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
      >>> _scope = []

      >>> _out = StringIO(); stream = CodeIO()
      >>> tag = Tag('div', dict(alt=expression(repr('Hello World!'))))
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

    def __init__(self, tag, attributes, selfclosing=False):
        i = tag.find('}')
        if i != -1:
            self.tag = tag[i+1:]
        else:
            self.tag = tag

        self.selfclosing = selfclosing
        self.attributes = attributes
        
    def begin(self, stream):
        stream.out('<%s' % self.tag)

        # attributes
        for attribute, expression in self.attributes.items():
            stream.out(' %s="' % attribute)
            write = Write(expression)
            write.begin(stream)
            write.end(stream)
            stream.out('"')

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
      >>> _scope = []

    We need to set up the repeat object.

      >>> from z3c.pt import utils
      >>> repeat = utils.repeatdict()

    Simple repeat loop and repeat data structure:

      >>> _repeat = Repeat("i", expression("range(5)"))
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
        self.define = Define(v, expression("None"), scope)
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
      >>> write = Write(expression("'New York'"))
      >>> write.begin(stream)
      >>> write.end(stream)
      >>> exec stream.getvalue()
      >>> _out.getvalue()
      'New York'
      >>> _out = StringIO()
      >>> write = Write(expression("undefined | ', New York!'"))
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
            stream.write("_out.write(%s)" % self.expressions[0])
        else:
            self.assign.begin(stream, temp)
            stream.write("_out.write(%s)" % temp)
        
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
