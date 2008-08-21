from compiler import ast, parse
from compiler.pycodegen import ModuleCodeGenerator

from transformer import ASTTransformer

import __builtin__

CONSTANTS = frozenset(['False', 'True', 'None', 'NotImplemented', 'Ellipsis'])
UNDEFINED = object()

def flatten(list):
    """Flattens a potentially nested sequence into a flat list.
    """
    l = []
    for elt in list:
        t = type(elt)
        if t is set or t is tuple or t is list or t is frozenset:
            for elt2 in flatten(elt):
                l.append(elt2)
        else:
            l.append(elt)
    return l

class Lookup(object):
    """Abstract base class for variable lookup implementations."""

    @classmethod
    def globals(cls):
        """Construct the globals dictionary to use as the execution context for
        the expression or suite.
        """
        return {
            '_lookup_attr': cls.lookup_attr,
            '_lookup_name': cls.lookup_name,
        }

    @classmethod
    def lookup_attr(cls, obj, key):
        try:
            return getattr(obj, key)
        except AttributeError, e:
            try:
                return obj[key]
            except (KeyError, TypeError):
                raise e

    @classmethod
    def lookup_name(cls, data, name):
        try:
            return data[name]
        except KeyError:
            raise NameError(name)

class TemplateASTTransformer(ASTTransformer):
    """Concrete AST transformer that implements the AST transformations needed
    for code embedded in templates.

    """

    def __init__(self, globals):
        self.locals = [CONSTANTS]
        builtin = dir(__builtin__)
        self.locals.append(set(globals))
        self.locals.append(set(builtin))
        # self.names is an optimization for visitName (so we don't
        # need to flatten the locals every time it's called)
        self.names = set()
        self.names.update(CONSTANTS)
        self.names.update(builtin)
        self.names.update(globals)

    def visitConst(self, node):
        if isinstance(node.value, unicode):
            return ast.Const(node.value.encode('utf-8'))
        return node

    def visitAssName(self, node):
        if len(self.locals) > 1:
            if node.flags == 'OP_ASSIGN':
                self.locals[-1].add(node.name)
                self.names.add(node.name)
            else:
                self.locals[-1].remove(node.name)
                self.names.remove(node.name)
        return node

    def visitClass(self, node):
        if len(self.locals) > 1:
            self.locals[-1].add(node.name)
            self.names.add(node.name)
        self.locals.append(set())
        try:
            return ASTTransformer.visitClass(self, node)
        finally:
            self.locals.pop()

    def visitFor(self, node):
        self.locals.append(set())
        try:
            return ASTTransformer.visitFor(self, node)
        finally:
            self.locals.pop()

    def visitFunction(self, node):
        if len(self.locals) > 1:
            self.locals[-1].add(node.name)
            self.names.add(node.name)
        self.locals.append(set(node.argnames))
        self.names.update(node.argnames)
        try:
            return ASTTransformer.visitFunction(self, node)
        finally:
            self.locals.pop()

    def visitGenExpr(self, node):
        self.locals.append(set())
        try:
            return ASTTransformer.visitGenExpr(self, node)
        finally:
            self.locals.pop()

    def visitLambda(self, node):
        argnames = flatten(node.argnames)
        self.names.update(argnames)
        self.locals.append(set(argnames))
        try:
            return ASTTransformer.visitLambda(self, node)
        finally:
            self.locals.pop()

    def visitListComp(self, node):
        self.locals.append(set())
        try:
            return ASTTransformer.visitListComp(self, node)
        finally:
            self.locals.pop()

    def visitName(self, node):
        # If the name refers to a local inside a lambda, list comprehension, or
        # generator expression, leave it alone
        if not node.name in self.names:
            # Otherwise, translate the name ref into a context lookup
            func_args = [ast.Name('_scope'), ast.Const(node.name)]
            node = ast.CallFunc(ast.Name('_lookup_name'), func_args)
        return node

    def visitGetattr(self, node):
        """Get attribute with fallback to dictionary lookup.

        Note: Variables starting with an underscore are exempt
        (reserved for internal use).
        """
        
        if hasattr(node.expr, 'name') and node.expr.name.startswith('_'):
            return ast.Getattr(node.expr, node.attrname)

        return ast.CallFunc(ast.Name('_lookup_attr'), [
            self.visit(node.expr), ast.Const(node.attrname)
            ])

class Suite(object):
    __slots__ = ['code', '_globals']

    mode = 'exec'
    
    def __init__(self, source, globals=()):
        """Create the code object from a string."""

        node = parse(source, self.mode)

        # build tree
        transform = TemplateASTTransformer(globals)
        tree = transform.visit(node)
        filename = tree.filename = '<script>'

        # generate code
        gen = ModuleCodeGenerator(tree)
        gen.optimized = True

        self._globals = Lookup.globals()
        self.code = gen.getCode()

    def __hash__(self):
        return hash(self.code)

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self.code)
