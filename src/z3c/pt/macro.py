class Macro(object):
    def __init__(self, render):
        self.render = render
        
class Macros(object):
    def __init__(self, render):
        self.render = render

    def __getitem__(self, name):
        def render(**kwargs):
            return self.render(macro=name, **kwargs)
        return Macro(render)
