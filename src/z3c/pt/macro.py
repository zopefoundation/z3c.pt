class Macro(object):
    def __init__(self, render):
        self.render = render

class Macros(object):
    def __init__(self, render_macro):
        self.render = render_macro

    def __getitem__(self, name):
        def render(**kwargs):
            return self.render(name, parameters=kwargs)
        return Macro(render)
