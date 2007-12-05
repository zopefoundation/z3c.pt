from compiler import ast, parse
from compiler.pycodegen import ModuleCodeGenerator

from transformer import ASTTransformer

marker = object()

CONSTANTS = frozenset(['False', 'True', 'None', 'NotImplemented', 'Ellipsis'])

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

        expr = self.visit(node.expr)
        name = ast.Const(node.attrname)

        # hasattr(obj, key) and getattr(obj, key) or not
        # hasattr(obj, key) and obj[key]
        return ast.Or([ast.And(
            [ast.CallFunc(ast.Name('hasattr'), [expr, name], None, None),
             ast.CallFunc(ast.Name('getattr'), [expr, name], None, None)]),
                    ast.And([
            ast.Not(ast.CallFunc(ast.Name('hasattr'), [expr, name], None, None)),
            ast.Subscript(expr, 'OP_APPLY', [name])])])
    
class Suite(object):
    __slots__ = ['code']

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

        self.code = gen.getCode()
        
    def __hash__(self):
        return hash(self.code)

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self.source)
