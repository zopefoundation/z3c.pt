import errno
import os.path

from z3c.pt.pagetemplate import PageTemplateFile
from z3c.pt.texttemplate import TextTemplateFile

from chameleon.core import loader

class TemplateLoader(loader.TemplateLoader):
    def load_page(self, filename):
        return self.load(filename, PageTemplateFile)

    def load_text(self, filename):
        return self.load(filename, TextTemplateFile)

