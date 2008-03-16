from zope import interface

class IExpressionTranslation(interface.Interface):
    """This interface defines an expression translation utility."""
    
    def name(string):
        """Should interpret ``string`` as a name. This method will
        usually be the identity function."""
    
    def value(string):
        """Translate ``string`` to a value-expression tuple.

        Specification:

           value :: = expression [ |* value ]
           expresion ::= an expression string

           *) Using | as _logical or_ is not supported.

        """

    def validate(string):
        """Raises exception if ``string`` is not a valid exception."""

    def translate(string):
        """Translates ``string``."""
        
    def search(string):
        """Extracts the longest valid expression from the beginning of
        the provided string."""

    def variable(string):
        """A variable definition.
        
        Specification:
        
           variables :: = variable_name [, variables]

        """
        
    def mapping(string):
        """A mapping definition."""

    def definition(string):
        """A definition."""

    def definitions(string):
        """Multiple definitions.
        
        Specification:

           argument ::= define_var [';' define_var]
           define_var ::= Name python_expression
           
        """
