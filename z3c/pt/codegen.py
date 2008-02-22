from compiler import ast, parse
from compiler.pycodegen import ModuleCodeGenerator

from transformer import ASTTransformer

marker = object()

CONSTANTS = frozenset(['False', 'True', 'None', 'NotImplemented', 'Ellipsis'])

UNDEFINED = object()

class Lookup(object):
    """Abstract base class for variable lookup implementations."""

    def globals(cls):
        """Construct the globals dictionary to use as the execution context for
        the expression or suite.
        """
        return {
            '_lookup_attr': cls.lookup_attr,
        }

    globals = classmethod(globals)

    @classmethod
    def lookup_attr(cls, obj, key):
        __traceback_hide__ = True
        val = getattr(obj, key, UNDEFINED)
        if val is UNDEFINED:
            try:
                val = obj[key]
            except (KeyError, TypeError):
                raise AttributeError(key)

        return val

class TemplateASTTransformer(ASTTransformer):
    def __init__(self):
        self.locals = [CONSTANTS]
        
    def visitGetattr(self, node):
        """
        Allow fallback to dictionary lookup if attribute does not exist.

        Variables starting with an underscore are exempt.

        """
        
        if hasattr(node.expr, 'name') and node.expr.name.startswith('_'):
            return ast.Getattr(node.expr, node.attrname)

        return ast.CallFunc(ast.Name('_lookup_attr'), [
            self.visit(node.expr), ast.Const(node.attrname)
            ])
    
class Suite(object):
    __slots__ = ['code', '_globals']

    xform = TemplateASTTransformer
    mode = 'exec'
    
    def __init__(self, source):
        """Create the code object from a string."""

        node = parse(source, self.mode)

        # build tree
        transform = self.xform()
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
        return '%s(%r)' % (self.__class__.__name__, self.source)
