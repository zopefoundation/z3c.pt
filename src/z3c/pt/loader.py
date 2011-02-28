from z3c.pt.pagetemplate import PageTemplateFile

from chameleon import loader


class TemplateLoader(loader.TemplateLoader):
    def load_page(self, filename):
        return self.load(filename, PageTemplateFile)
