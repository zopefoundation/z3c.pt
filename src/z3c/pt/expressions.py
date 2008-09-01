import zope.interface
import zope.component
import zope.security
import zope.security.proxy
import zope.traversing.adapters

import parser
import re

import interfaces
import types
import config

_marker = object()

class ExpressionTranslation(object):
    zope.interface.implements(interfaces.IExpressionTranslation)

    re_pragma = re.compile(r'^\s*(?P<pragma>[a-z]+):\s*')
    re_interpolation = re.compile(r'(?P<prefix>[^\\]\$|^\$)({((?P<expression>.*)})?|(?P<variable>[A-Za-z][A-Za-z0-9_]*))')
    re_method = re.compile(r'^(?P<name>[A-Za-z0-9_]+)'
                           '(\((?P<args>[A-Za-z0-9_]+\s*(,\s*[A-Za-z0-9_]+)*)\))?')

    def name(self, string):
        return string
    
    def search(self, string):
        """
        We need to implement a ``validate``-method. Let's define that an
        expression is valid if it contains an odd number of
        characters.
        
          >>> class MockExpressionTranslation(ExpressionTranslation):
          ...     def validate(self, string):
          ...         if len(string) % 2 == 0: raise SyntaxError()

          >>> search = MockExpressionTranslation().search
          >>> search("a")
          'a'
          >>> search("ab")
          'a'
          >>> search("abc")
          'abc'
          
        """

        left = 0
        right = left + 1

        current = None

        while right <= len(string):
            expression = string[left:right]

            try:
                e = self.validate(expression)
                current = expression
            except SyntaxError, e:
                if right == len(string):
                    if current is not None:
                        return current

                    raise e

            right += 1

        return current

    def declaration(self, string):
        """
          >>> declaration = ExpressionTranslation().declaration

        Single variable:

          >>> declaration("variable")
          declaration('variable')

        Multiple variables:

          >>> declaration("variable1, variable2")
          declaration('variable1', 'variable2')

        Repeat not allowed:

          >>> declaration('repeat')
          Traceback (most recent call last):
          ...
          ValueError: Invalid variable name 'repeat' (reserved).

          >>> declaration('_disallowed')
          Traceback (most recent call last):
          ...
          ValueError: Invalid variable name '_disallowed' (starts with an underscore).
        """

        variables = []
        for var in string.split(', '):
            var = var.strip()

            if var in ('repeat',):
                raise ValueError, "Invalid variable name '%s' (reserved)." % var

            if var.startswith('_') and not var.startswith('_tmp'):
                raise ValueError(
                    "Invalid variable name '%s' (starts with an underscore)." % var)

            variables.append(var)

        return types.declaration(variables)

    def mapping(self, string):
        """
          >>> mapping = ExpressionTranslation().mapping
          
          >>> mapping("abc def")
          mapping(('abc', 'def'),)

          >>> mapping("abc def;")
          mapping(('abc', 'def'),)

          >>> mapping("abc")
          mapping(('abc', None),)

          >>> mapping("abc;")
          mapping(('abc', None),)

          >>> mapping("abc; def ghi")
          mapping(('abc', None), ('def', 'ghi'))

        """

        defs = string.split(';')
        mappings = []
        for d in defs:
            d = d.strip()
            if d == '':
                continue

            while '  ' in d:
                d = d.replace('  ', ' ')

            parts = d.split(' ')
            if len(parts) == 1:
                mappings.append((d, None))
            elif len(parts) == 2:
                mappings.append((parts[0], parts[1]))
            else:
                raise ValueError, "Invalid mapping (%s)." % string

        return types.mapping(mappings)

    def definitions(self, string):
        """
        
        >>> class MockExpressionTranslation(ExpressionTranslation):
        ...     def validate(self, string):
        ...         if string == '' or ';' in string:
        ...             raise SyntaxError()
        ...
        ...     def expression(self, string):
        ...         self.validate(string)
        ...         return types.value(string.strip())
        
        >>> definitions = MockExpressionTranslation().definitions
        
        Single define:
        
        >>> definitions("variable expression")
        definitions((declaration('variable'), value('expression')),)
        
        Multiple defines:
        
        >>> definitions("variable1 expression1; variable2 expression2")
        definitions((declaration('variable1'), value('expression1')),
                    (declaration('variable2'), value('expression2')))
        
        Tuple define:
        
        >>> definitions("(variable1, variable2) (expression1, expression2)")
        definitions((declaration('variable1', 'variable2'),
                    value('(expression1, expression2)')),)

        Global defines:

        >>> definitions("global variable expression")
        definitions((declaration('variable', global_scope=True), value('expression')),)

        Space, the 'in' operator and '=' may be used to separate
        variable from expression.

        >>> definitions("variable in expression")
        definitions((declaration('variable'), value('expression')),)        
        
        >>> definitions("variable1 = expression1; variable2 = expression2")
        definitions((declaration('variable1'), value('expression1')),
                    (declaration('variable2'), value('expression2')))

        >>> definitions("variable1=expression1; variable2=expression2")
        definitions((declaration('variable1'), value('expression1')),
                    (declaration('variable2'), value('expression2')))
        
        A define clause that ends in a semicolon:
        
        >>> definitions("variable expression;")
        definitions((declaration('variable'), value('expression')),)
        
        A define clause with a trivial expression (we do allow this):
        
        >>> definitions("variable")
        definitions((declaration('variable'), None),)
        
        A proper define clause following one with a trivial expression:
        
        >>> definitions("variable1 expression; variable2")
        definitions((declaration('variable1'), value('expression')),
                    (declaration('variable2'), None))

        """

        string = string.replace('\n', '').strip()

        defines = []
        i = 0
        while i < len(string):
            global_scope = False
            if string.startswith('global'):
                global_scope = True
                i += 6

            while string[i] == ' ':
                i += 1

            # get variable definition
            if string[i] == '(':
                j = string.find(')', i+1)
                if j == -1:
                    raise ValueError, "Invalid variable tuple definition (%s)." % string
                var = self.declaration(string[i+1:j])
                j += 1
            else:
                j = string.find('=', i + 1)
                k = string.find(' ', i + 1)
                if k < j and k > -1 or j < 0:
                    j = k
                
                if j < 0:
                    var = self.declaration(string[i:])
                    j = len(string)
                else:
                    var = self.declaration(string[i:j])

            var.global_scope = global_scope
            
            # get expression
            i = j + len(string) - j - len(string[j:].lstrip())

            token = string[i:]
            if token.startswith('=='):
                raise ValueError("Invalid variable definition (%s)." % string)
            elif token.startswith('='):
                i += 1
            elif token.startswith('in'):
                i += 2

            try:
                expr = self.expression(string[i:])
                j = -1
            except SyntaxError, e:
                expr = None
                j = len(string)
            
            while j > i:
                j = string.rfind(';', i, j)
                if j < 0:
                    raise e

                try:
                    expr = self.expression(string[i:j])
                except SyntaxError, e:
                    if string.rfind(';', i, j) > 0:
                        continue
                    raise e
                
                break
                
            defines.append((var, expr))

            if j < 0:
                break
            
            i = j + 1

        return types.definitions(defines)

    def definition(self, string):
        defs = self.definitions(string)
        if len(defs) != 1:
            raise ValueError, "Multiple definitions not allowed."

        return defs[0]

    def output(self, string):
        """
        >>> class MockExpressionTranslation(ExpressionTranslation):
        ...     def validate(self, string):
        ...         return True
        ...
        ...     def translate(self, string):
        ...         return types.value(string)

        >>> output = MockExpressionTranslation().output

        >>> output("context/title")
        escape(value('context/title'),)

        >>> output("context/pretty_title_or_id|context/title")
        escape(value('context/pretty_title_or_id'), value('context/title'))

        >>> output("structure context/title")
        value('context/title')
        
        """
        
        if string.startswith('structure '):
            return self.expression(string[len('structure'):])
        
        expression = self.expression(string)

        if isinstance(expression, types.parts):
            return types.escape(expression)

        return types.escape((expression,))
            
    def expression(self, string):
        """We need to implement the ``validate`` and
        ``translate``-methods. Let's define that an expression is
        valid if it contains an odd number of characters.
        
        >>> class MockExpressionTranslation(ExpressionTranslation):
        ...     def validate(self, string):
        ...         return True
        ...
        ...     def translate(self, string):
        ...         return types.value(string)

        >>> expression = MockExpressionTranslation().expression

        >>> expression('a')
        value('a')

        >>> expression('a|b')
        parts(value('a'), value('b'))
    
        """

        string = string.replace('\n', '').strip()

        if not string:
            return types.parts()

        parts = []

        # default translator is ``self``
        translator = self

        i = j = 0
        while i < len(string):
            if translator is self:
                match = self.re_pragma.match(string[i:])
                if match is not None:
                    pragma = match.group('pragma')

                    translator = \
                        zope.component.queryUtility(
                            interfaces.IExpressionTranslation, name=pragma) or \
                        zope.component.queryAdapter(
                            self, interfaces.IExpressionTranslation, name=pragma)
                    
                    if translator is not None:
                        i += match.end()
                        continue

                    translator = self

            j = string.find('|', j + 1)
            if j == -1:
                j = len(string)

            expr = string[i:j].lstrip()

            try:
                translator.validate(expr)
            except Exception, e:
                if j < len(string):
                    continue

                raise e

            value = translator.translate(expr)
            parts.append(value)
            translator = self
            
            i = j + 1

        if len(parts) == 1:
            return parts[0]

        return types.parts(parts)

    def interpolate(self, string):
        """Search for an interpolation and return a match.

        >>> class MockExpressionTranslation(ExpressionTranslation):
        ...     def validate(self, string):
        ...         if '}' in string: raise SyntaxError
        ...
        ...     def translate(self, string):
        ...         return types.value(string)

        >>> interpolate = MockExpressionTranslation().interpolate
        
        >>> interpolate('${abc}').group('expression')
        'abc'

        >>> interpolate('abc${def}').group('expression')
        'def'

        >>> interpolate('abc${def}ghi${jkl}').group('expression')
        'def'

        >>> interpolate('$abc').group('variable')
        'abc'

        >>> interpolate('${abc')
        Traceback (most recent call last):
          ...
        SyntaxError: Interpolation expressions must be of the form ${<expression>} (${abc)
        
        """

        m = self.re_interpolation.search(string)
        if m is None:
            return None

        expression = m.group('expression')
        variable = m.group('variable')
        
        if expression:
            left = m.start()+len(m.group('prefix'))
            match = string[left+1:]

            while match:
                try:
                    exp = self.expression(match)
                    break
                except SyntaxError:
                    match = match[:-1]
            else:
                raise

            string = string[:left+1+len(match)]+'}'
            return self.re_interpolation.search(string)

        if m is None or (expression is None and variable is None):
            raise SyntaxError(
                "Interpolation expressions must be of the "
                "form ${<expression>} (%s)" % string)

        if expression and not m.group('expression'):
            raise SyntaxError(expression)

        return m

    def method(self, string):
        """Parse a method definition.

        >>> method = ExpressionTranslation().method

        >>> method('name')
        name()

        >>> method('name(a, b, c)')
        name(a, b, c)
        
        """

        m = self.re_method.match(string)
        if m is None:
            raise ValueError("Not a valid method definition (%s)." % string)

        name = m.group('name')
        args = [arg.strip() for arg in (m.group('args') or "").split(',') if arg]

        return types.method(name, args)
        
class PythonTranslation(ExpressionTranslation):
    def validate(self, string):
        """We use the ``parser`` module to determine if
        an expression is a valid python expression."""
        
        parser.expr(string.encode('utf-8'))

    def translate(self, string):
        if isinstance(string, unicode):
            string = string.encode('utf-8')

        return types.value(string)

python_translation = PythonTranslation()

class StringTranslation(ExpressionTranslation):
    zope.component.adapts(interfaces.IExpressionTranslation)

    def __init__(self, translator):
        self.translator = translator

    def validate(self, string):
        self.interpolate(string)
        self.split(string)

    def translate(self, string):
        return types.join(self.split(string))
        
    def split(self, string):
        """Split up an interpolation string expression into parts that
        are either unicode strings or ``value``-tuples.

        >>> class MockTranslation(ExpressionTranslation):
        ...     def validate(self, string):
        ...         if '}' in string: raise SyntaxError
        ...
        ...     def translate(self, string):
        ...         return types.value(string)
        
        >>> class MockStringTranslation(StringTranslation):
        ...     pass
        
        >>> split = MockStringTranslation(MockTranslation()).split

        >>> split("${abc}")
        (value('abc'),)

        >>> split("abc${def}")
        ('abc', value('def'))

        >>> split("${def}abc")
        (value('def'), 'abc')

        >>> split("abc${def}ghi")
        ('abc', value('def'), 'ghi')

        >>> split("abc${def}ghi${jkl}")
        ('abc', value('def'), 'ghi', value('jkl'))

        >>> split("abc${def | ghi}")
        ('abc', parts(value('def '), value('ghi')))

        >>> print split("abc${La Pe\xc3\xb1a}")
        ('abc', value('La Pe\\xc3\\xb1a'))
        
        """

        m = self.translator.interpolate(string)
        if m is None:
            return (self._unescape(string),)

        parts = []
        
        start = m.start()
        if start > 0:
            text = string[:m.start()+1]
            parts.append(self._unescape(text))

        expression = m.group('expression')
        variable = m.group('variable')

        if expression:
            parts.append(self.translator.expression(expression))
        elif variable:
            parts.append(self.translator.expression(variable))
                
        rest = string[m.end():]
        if len(rest):
            parts.extend(self.split(rest))

        return tuple(parts)

    def definitions(self, string):
        """
        
        >>> definitions = StringTranslation(python_translation).definitions
        
        Semi-colon literal.
        
        >>> definitions("variable part1;; part2")
        definitions((declaration('variable'), join('part1; part2',)),)

        >>> definitions("variable1 part1;; part2; variable2 part3")
        definitions((declaration('variable1'), join('part1; part2',)),
                    (declaration('variable2'), join('part3',)))
    
        """

        return super(StringTranslation, self).definitions(string)

    def _unescape(self, string):
        i = string.rfind(';')
        if i > 0 and i != string.rfind(';'+';') + 1:
            raise SyntaxError(
                "Semi-colons in string-expressions must be escaped.")
        return string.replace(';;', ';')

class PathTranslation(ExpressionTranslation):
    path_regex = re.compile(
        r'^((nocall|not):\s*)*([A-Za-z_][A-Za-z0-9_]*)'+
        r'(/[A-Za-z_@-][A-Za-z0-9_@-\\.]*)*$')


    def validate(self, string):
        if not self.path_regex.match(string):
            raise SyntaxError("Not a valid path-expression.")

    def translate(self, string):
        """
            >>> translate = PathTranslation().translate
            >>> translate("a/b")
            value("_path(a, request, True, 'b')")

            >>> translate("context/@@view")
            value("_path(context, request, True, '@@view')")

            >>> translate("nocall: context/@@view")
            value("_path(context, request, False, '@@view')")

            >>> translate("not: context/@@view")
            value("not(_path(context, request, True, '@@view'))")

        """

        nocall = False
        negate = False

        while string:
            m = self.re_pragma.match(string)
            if m is None:
                break

            string = string[m.end():]
            pragma = m.group('pragma').lower()

            if pragma == 'nocall':
                nocall = True
            elif pragma == 'not':
                negate = True
            else:
                raise ValueError("Invalid pragma: %s" % pragma)

        parts = string.split('/')

        # map 'nothing' to 'None'
        parts = map(lambda part: part == 'nothing' and 'None' or part, parts)
        
        base = parts[0]
        components = [repr(part) for part in parts[1:]]

        if not components:
            components = ()

        value = types.value(
            '%s(%s, request, %s, %s)' % \
            (config.SYMBOLS.path, base, not nocall, ', '.join(components)))

        if negate:
            value = types.value('not(%s)' % value)

        value.symbol_mapping[config.SYMBOLS.path] = path_traverse

        return value

def path_traverse(base, request, call, *path_items):
    """See ``zope.app.pagetemplate.engine``."""

    _callable = callable(base)

    for i in range(len(path_items)):
        name = path_items[i]

        next = getattr(base, name, _marker)
        if next is not _marker:
            _callable = callable(next)

            if _callable:
                base = next()
            else:
                base = next
                continue
        else:
            # special-case dicts for performance reasons        
            if getattr(base, '__class__', None) == dict:
                base = base[name]
            else:
                base = zope.traversing.adapters.traversePathElement(
                    base, name, path_items[i+1:], request=request)

        _callable = callable(base)

        if not isinstance(base, (basestring, tuple, list)):
            base = zope.security.proxy.ProxyFactory(base)

    if call and _callable:
        base = base()

    return base

path_translation = PathTranslation()
