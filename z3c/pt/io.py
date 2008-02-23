from StringIO import StringIO

class CodeIO(StringIO):
    """
    A high-level I/O class to write Python code to a stream.
    Indentation is managed using ``indent`` and ``outdent``.

    Also:
    
    * Convenience methods for keeping track of temporary
    variables (see ``save``, ``restore`` and ``getvariable``).

    * Methods to process clauses (see ``begin`` and ``end``).
    
    """

    t_prefix = '_tmp'
    v_prefix = '_var'
    
    def __init__(self, indentation=0, indentation_string="\t"):
        StringIO.__init__(self)
        self.indentation = indentation
        self.indentation_string = indentation_string
        self.queue = u''
        self.scope = [set()]
        
        self._variables = {}
        self.t_counter = 0

    def save(self):
        self.t_counter += 1
        return "%s%d" % (self.t_prefix, self.t_counter)
        
    def restore(self):
        var = "%s%d" % (self.t_prefix, self.t_counter)
        self.t_counter -= 1
        return var
        
    def indent(self, amount=1):
        if amount > 0:
            self.cook()
            self.indentation += amount

    def outdent(self, amount=1):
        if amount > 0:
            self.cook()
            self.indentation -= amount

    def out(self, string):
        self.queue += string

    def cook(self):
        if self.queue:
            queue = self.queue
            self.queue = ''
            self.write("_out.write('%s')" %
                       queue.replace('\n', '\\n').replace("'", "\\'"))
        
    def write(self, string):
        self.cook()
        StringIO.write(
            self, self.indentation_string * self.indentation + string + '\n')

    def getvalue(self):
        self.cook()
        return StringIO.getvalue(self)

    def begin(self, clauses):
        if isinstance(clauses, (list, tuple)):
            for clause in clauses:
                self.begin(clause)
        else:
            clauses.begin(self)
            
    def end(self, clauses):
        if isinstance(clauses, (list, tuple)):
            for clause in reversed(clauses):
                self.end(clause)
        else:
            clauses.end(self)
        
