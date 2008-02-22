import parser

def name(string):
    return string
    
def value(string):
    """
    Specification:

    value :: = python_expression [ |* value ]
    python_expresion ::= a python expression string

    *) Using | as logical or is not supported.

      >>> value("4 + 5")
      ['4 + 5']

    Complex expressions:

      >>> value("a.non_defined_method() | 1")
      ['a.non_defined_method() ', '1']

    Expression with non-semantic horizontal bar.

      >>> value("'|'")
      ["'|'"]

    Expression with non-semantic horizontal bar and semantic bar.

      >>> value("a.non_defined_method() | '|'")
      ['a.non_defined_method() ', "'|'"]

    """

    string = string.replace('\n', '').strip()

    if not string:
        return []
        
    expressions = []

    i = j = 0
    while i < len(string):
        j = string.find('|', j + 1)
        if j == -1:
            j = len(string)

        expr = string[i:j].lstrip()

        try:
            # we use the ``parser`` module to determine if
            # an expression is a valid python expression
            parser.expr(expr.encode('utf-8'))
        except SyntaxError, e:
            if j < len(string):
                continue

            raise e
            
        expressions.append(expr)
        i = j + 1

    return expressions

def variable(string):
    """
    Specification:
    
    variables :: = variable_name [, variables]

    Single variable:

      >>> variable("variable")
      ('variable',)

    Multiple variables:

      >>> variable("variable1, variable2")
      ('variable1', 'variable2')
      
    """

    variables = []
    for var in string.split(', '):
        var = var.strip()

        if var in ('repeat',):
            raise ValueError, "Invalid variable name '%s' (reserved)." % variable

        if var.startswith('_'):
            raise ValueError, \
                  "Invalid variable name '%s' (starts with an underscore)." % variable            
        variables.append(var)

    return tuple(variables)

def mapping(string):
    """

      >>> mapping("abc def")
      [('abc', 'def')]

      >>> mapping("abc")
      [('abc', None)]

      >>> mapping("abc; def ghi")
      [('abc', None), ('def', 'ghi')]

    """

    defs = string.split(';')
    mappings = []
    for d in defs:
        d = d.strip()
        while '  ' in d:
            d = d.replace('  ', ' ')

        parts = d.split(' ')
        if len(parts) == 1:
            mappings.append((d, None))
        elif len(parts) == 2:
            mappings.append((parts[0], parts[1]))
        else:
            raise ValueError, "Invalid mapping (%s)." % string

    return mappings
    
def definitions(string):
    """
    Specification:

    argument ::= define_var [';' define_var]
    define_var ::= Name python_expression

    Single define:

      >>> definitions("variable expression")
      [(['variable'], ['expression'])]
    
    Multiple defines:

      >>> definitions("variable1 expression1; variable2 expression2")
      [(['variable1'], ['expression1']), (['variable2'], ['expression2'])]

    Tuple define:

      >>> definitions("(variable1, variable2) (expression1, expression2)")
      [(['variable1', 'variable2'], ['(expression1, expression2)'])]

    Use of unescaped semicolon in an expression:

      >>> definitions("variable ';'")
      [(['variable'], ["';'"])]
    
    A define clause that ends in a semicolon:

      >>> definitions("variable expression;")
      [(['variable'], ['expression'])]

    A define clause with a trivial expression (we do allow this):
    
      >>> definitions("variable")
      [(['variable'], None)]

    A proper define clause following one with a trivial expression:

      >>> definitions("variable1 expression; variable2")
      [(['variable1'], ['expression']), (['variable2'], None)]
      
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
                var = variable(string[i:])
                j = len(string)
            else:
                var = variable(string[i:j])

        # get expression
        i = j
        while j < len(string):
            j = string.find(';', j+1)
            if j == -1:
                j = len(string)

            try:
                expr = value(string[i:j])
            except SyntaxError, e:
                if j < len(string):
                    continue
                raise e
            break
        else:
            expr = None

        defines.append((list(var), expr))

        i = j + 1

    return defines

def definition(string):
    defs = definitions(string)
    if len(defs) != 1:
        raise ValueError, "Multiple definitions not allowed."

    return defs[0]
