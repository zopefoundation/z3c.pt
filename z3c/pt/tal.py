import parser
import cgi
import xml.sax.saxutils
import itertools

def expression(string):
    """
    Python-expressions in try-except construct.
    
    Specification:

    expression :: = python_expression [ |* expression ]
    python_expresion ::= a python expression string

    *) Using | as logical or is not supported.

    """

    string = string.replace('\n', '')

    expression = []

    i = j = 0
    while i < len(string):
        j = string.find('|', j + 1)
        if j == -1:
            j = len(string)

        expr = string[i:j].lstrip()

        try:
            # we use the ``parser`` module to determine if
            # an expression is a valid python expression
            parser.expr(expr)
        except SyntaxError, e:
            if j < len(string):
                continue

            raise e

        expression.append(expr)
        i = j + 1

    return expression

def variable(string):
    for var in string.split(', '):
        var = var.strip()

        if var in ('repeat',):
            raise ValueError, "Invalid variable name '%s' (reserved)." % variable

        if var.startswith('_'):
            raise ValueError, \
                  "Invalid variable name '%s' (starts with an underscore)." % variable            
        yield var
    
def definition(string):
    """
    TAL define-expression:

    Specification:

    argument ::= define_var [';' define_var]
    define_var ::= Name python_expression

    """

    string = string.replace('\n', '').strip()

    defines = []

    i = 0
    while i < len(string):
        while string[i] == ' ':
            i += 1

        # get variable definition
        if string[i] == '(':
            j = string.find(')', i+1)
            if j == -1:
                raise ValueError, "Invalid variable tuple definition (%s)." % string
            var = variable(string[i+1:j])
            j += 1
        else:
            j = string.find(' ', i + 1)
            if j == -1:
                raise ValueError, "Invalid define clause (%s)." % string
            var = variable(string[i:j])

        # get expression
        i = j
        while j < len(string):
            j = string.find(';', j+1)
            if j == -1:
                j = len(string)

            try:
                expr = expression(string[i:j])
            except SyntaxError, e:
                continue
            break
        else:
            raise e

        defines.append((list(var), expr))

        i = j + 1

    return defines

class repeatitem(object):
    def __init__(self, iterator, length):
        self.length = length
        self.iterator = iterator
        
    @property
    def index(self):
        return self.length - len(self.iterator) - 1
        
    @property
    def start(self):
        return self.index == 0

    @property
    def end(self):
        return self.index == self.length - 1

    def number(self):
        return self.index + 1

    def odd(self):
        return bool(self.index % 2)

    def even(self):
        return not self.odd()

class repeatdict(dict):
    def __setitem__(self, key, iterator):
        try:
            length = len(iterator)
        except TypeError:
            length = None
            
        dict.__setitem__(self, key, (iterator, length))
        
    def __getitem__(self, key):
        value, length = dict.__getitem__(self, key)

        if not isinstance(value, repeatitem):
            value = repeatitem(value, length)
            self.__setitem__(key, value)

        return value
    
class Assign(object):
    def __init__(self, expression):
        self.expressions = expression
            
    def begin(self, stream, variable):
        """First n - 1 expressions must be try-except wrapped."""

        for expression in self.expressions[:-1]:
            stream.write("try:")
            stream.indent()
            stream.write("%s = %s" % (variable, expression))
            stream.outdent()
            stream.write("except Exception, e:")
            stream.indent()

        expression = self.expressions[-1]
        stream.write("%s = %s" % (variable, expression))

    def end(self, stream):
        stream.outdent(len(self.expressions)-1)

class Define(object):    
    def __init__(self, value):
        self.defines = [(v, Assign(e)) for v, e in definition(value)]
        self.variables = list(itertools.chain(*[v for (v, e) in self.defines]))

    def update(self, node):
        return node
            
    def begin(self, stream):
        # save local variables already in scope
        save = stream.save()
        stream.write("%s = {}" % save)

        for var in self.variables:
            stream.write("if '%s' in _scope: %s['%s'] = %s" % (var, save, var, var))
            stream.write("else: _scope.append('%s')" % var)
        
        for variables, assign in self.defines:
            if len(variables) == 1:
                assign.begin(stream, variables[0])
            else:
                assign.begin(stream, u"(%s,)" % ", ".join(variables))
            assign.end(stream)
        
    def end(self, stream):
        restore = stream.restore()

        for variable in reversed(self.variables):
            # restore local variables previously in scope
            stream.write("if '%s' in %s:" % (variable, restore))
            stream.indent()
            stream.write("%s = %s['%s']" % (variable, restore, variable))
            stream.outdent()
            stream.write("else:")
            stream.indent()
            stream.write("del %s" % variable)
            stream.write("_scope.remove('%s')" % variable)
            stream.outdent()
            
class Condition(object):
    def __init__(self, value):
        self.assign = Assign(expression(value))

    def update(self, node):
        return node

    def begin(self, stream):
        variable = '_condition'

        self.assign.begin(stream, variable)
        stream.write("if %s:" % variable)
        stream.indent()

    def end(self, stream):
        self.assign.end(stream)
        stream.outdent()

class Repeat(object):
    def __init__(self, value):
        string = value.lstrip().replace('\n', '')

        space = string.find(' ')
        if space == -1:
            raise ValueError, "Invalid repeat clause (%s)." % value

        self.variable = string[:space]
        self.assign = Assign(expression(string[space:]))
        
    def update(self, node):
        return node

    def begin(self, stream):
        variable = self.variable
        iterator = stream.save()
        
        self.assign.begin(stream, iterator)

        # define variable scope
        self.define = Define("%s None" % self.variable)
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
        
class Attribute(object):
    def __init__(self, value):
        self.attributes = [(v, Assign(e)) for v, e in definition(value)]

    def update(self, node):
        for variables, expression in self.attributes:
            for variable in variables:
                if variable in node.attrib:
                    del node.attrib[variable]

        return node
    
    def begin(self, stream):
        stream.write("_attrs = {}")
        for variables, assign in self.attributes:
            for variable in variables:
                assign.begin(stream, "_attrs['%s']" % variable)
                assign.end(stream)

    def end(self, stream):
        pass

class Content(object):
    def __init__(self, value):
        self.assign = Assign(expression(value))

    def update(self, node):
        node.text = ''
        for element in node.getchildren():
            node.remove(element)

        return node
        
    def begin(self, stream):
        self.assign.begin(stream, '_content')
        stream.write("_out.write(_content)")
        
    def end(self, stream):
        self.assign.end(stream)

class Replace(Content):
    def update(self, node):
        return None
    
class Tag(object):
    def __init__(self, node):
        self.node = node
        self.tail = node.tail
                
    @property
    def tag(self):
        tag = self.node.tag
        if tag.startswith('{'):
            return tag[tag.find('}')+1:]

        return tag

    def update(self, node):
        self.node = node
        return node
    
    def begin(self, stream):
        if self.node is None:
            return
        stream.out('<%s' % self.tag)
        stream.write("for _name, _value in _attrs.items():")
        stream.indent()
        stream.write("""_out.write(' %s=\"%s\"' % (_name, _escape(_value, '\"')))""")
        stream.outdent()
        stream.write("_attrs.clear()")
        for name, value in self.node.attrib.items():
            stream.out(' %s=%s' % (name, xml.sax.saxutils.quoteattr(value)))

        if self.node.text is None:
            stream.out(' />')
        else:
            stream.out('>')
        
        text = self.node.text
        if text is not None:
            text = cgi.escape(text.replace('\n', '\\n'), '"')
            stream.out(text)

    def end(self, stream):
        if self.node is not None and self.node.text is not None:
            stream.out('</%s>' % self.tag)

        if self.tail is not None:
            tail = cgi.escape(self.tail.replace('\n', '\\n'), "'")
            stream.out(tail)

def handler(key=None):
    def decorate(f):
        def g(node):
            if key is None:
                return f(node, None)
            return f(node, node.get(key))
        g.__ns__ = key
        return g
    return decorate

@handler("{http://xml.zope.org/namespaces/tal}define")
def define(node, value):
    return Define(value)

@handler("{http://xml.zope.org/namespaces/tal}condition")
def condition(node, value):
    return Condition(value)

@handler("{http://xml.zope.org/namespaces/tal}repeat")
def repeat(node, value):
    return Repeat(value)

@handler("{http://xml.zope.org/namespaces/tal}attributes")
def attribute(node, value):
    return Attribute(value)

@handler("{http://xml.zope.org/namespaces/tal}content")
def content(node, value):
    return Content(value)

@handler("{http://xml.zope.org/namespaces/tal}replace")
def replace(node, value):
    return Replace(value)

@handler("{http://xml.zope.org/namespaces/tal}omit-tag")
def omit(node, value):
    raise NotImplemented, "The tal:omit-tag statement is not supported yet."

@handler()
def tag(node, value):
    return Tag(node)
