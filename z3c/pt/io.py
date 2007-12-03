from StringIO import StringIO

class CodeIO(StringIO):
    """
    A high-level I/O class to write Python code to a stream.
    Indentation is managed using ``indent`` and ``outdent``.

    Convenience methods for keeping track of temporary
    variables.
    
    """

    variable_prefix = '_saved'
    
    def __init__(self, indentation_string="\t"):
        StringIO.__init__(self)
        self.indentation = 0
        self.indentation_string = indentation_string
        self.counter = 0
        self.queue = u''
    
    def save(self, variable=None):
        self.counter += 1
        if variable:
            self.write("%s%d = %s" % (self.variable_prefix, self.counter, variable))
        else:
            return "%s%d" % (self.variable_prefix, self.counter)
        
    def restore(self, variable=None):
        if variable:
            self.write("%s = %s%d" % (variable, self.variable_prefix, self.counter))
        else:
            return "%s%d" % (self.variable_prefix, self.counter)
        
        self.counter -= 1
        
    def indent(self, amount=1):
        self.indentation += amount

    def outdent(self, amount=1):
        self.indentation -= amount

    def out(self, string):
        self.queue += string

    def cook(self):
        if self.queue:
            queue = self.queue
            self.queue = ''
            self.write("_out.write('%s')" % queue)
        
    def write(self, string):
        self.cook()
        StringIO.write(self, self.indentation_string * self.indentation + string + '\n')

    def getvalue(self):
        self.cook()
        return StringIO.getvalue(self)
