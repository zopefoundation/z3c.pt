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
        self.scope = {}

        self.t_counter = 0
        self.v_counter = 0        

    def save(self, variable=None):
        self.t_counter += 1
        if variable:
            self.write("%s%d = %s" % (self.t_prefix, self.t_counter, variable))
        else:
            return "%s%d" % (self.t_prefix, self.t_counter)
        
    def restore(self, variable=None):
        if variable:
            self.write("%s = %s%d" % (variable, self.t_prefix, self.t_counter))
        else:
            return "%s%d" % (self.t_prefix, self.t_counter)
        
        self.t_counter -= 1

    def savevariable(self, obj, expression="None"):
        if obj in self.scope:
            return self.scope[obj]

        self.v_counter += 1
        variable = "%s%d" % (self.v_prefix, self.v_counter)

        self.write("%s = %s" % (variable, expression))

        self.scope[obj] = variable
        return variable

    def restorevariable(self, obj, expression="None"):
        if obj in self.scope:
            return self.scope[obj]

        variable = "%s%d" % (self.v_prefix, self.v_counter)
        self.v_counter -= 1

        self.scope[obj] = variable
        return variable

    def indent(self, amount=1):
        self.indentation += amount

    def outdent(self, amount=1):
        self.cook()
        self.indentation -= amount

    def out(self, string):
        self.cook()
        self.queue += string

    def cook(self):
        if self.queue:
            queue = self.queue
            self.queue = ''
            self.write("_out.write('%s')" % queue.replace('\n', '\\n'))
        
    def write(self, string):
        self.cook()
        StringIO.write(self, self.indentation_string * self.indentation + string + '\n')

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
        
