class expression:
    pass

class parts(tuple, expression):
    def __repr__(self):
        return 'parts'+tuple.__repr__(self)

class value(str, expression):            
    def __repr__(self):
        return 'value(%s)' % str.__repr__(self)

class template(value):
    def __repr__(self):
        return 'template(%s)' % str.__repr__(self)

class join(tuple, expression):
    def __repr__(self):
        return 'join'+tuple.__repr__(self)

class declaration(tuple):
    global_scope = False
    
    def __repr__(self):
        items = map(repr, self)
        if self.global_scope:
            items.append('global_scope=%s' % repr(self.global_scope))
        return 'declaration(%s)' % ', '.join(items)

class mapping(tuple):
    def __repr__(self):
        return 'mapping'+tuple.__repr__(self)

class definitions(tuple):
    def __repr__(self):
        return 'definitions'+tuple.__repr__(self)

class escape(parts):
    def __repr__(self):
        return 'escape'+tuple.__repr__(self)

class method(object):
    def __init__(self, name, args):
        self.name = name
        self.args = args

    def __repr__(self):
        return "%s(%s)" % (self.name, ", ".join(arg for arg in self.args))
        
