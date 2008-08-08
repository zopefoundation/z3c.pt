import errno
import os.path
from z3c.pt.pagetemplate import PageTemplateFile
from z3c.pt.texttemplate import TextTemplateFile

class TemplateLoader(object):
    """Template loader tool.
    """

    def __init__(self, search_path=None, auto_reload=False, cachedir=None):
        self.search_path = search_path is not None and search_path or []
        self.auto_reload = auto_reload
        self.cachedir = cachedir
        if cachedir is not None:
            if not os.path.isdir(cachedir):
                raise ValueError, "Invalid cachedir")


    def _load(self, filename, klass):
        if os.path.isabs(filename):
            return PageTemplateFile(filename)

        for path in self.search_path:
            path = os.path.join(path, filename)
            try:
                return klass(path, auto_reload=self.auto_reload,
                                cachedir=self.cachedir)
            except OSError, e:
                if e.errno!=erro.ENOENT:
                    raise

        raise ValueError("Can not find template %s" % filename)


    def load_page(self, filename):
        return self._load(filename, PageTemplateFile)


    def load_text(self, filename):
        return self._load(filename, TextTemplateFile)
