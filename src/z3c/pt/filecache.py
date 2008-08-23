import os
import config
import cPickle as pickle

class TemplateCache(object):
    def __init__(self, filename):
        self.filename = filename
        self.registry = {}
        self.load()
        
    def __getitem__(self, key):
        return self.registry[key]

    def __setitem__(self, key, template):
        self.registry[key] = template
        self.save()

    def __len__(self):
        return len(self.registry)
    
    def get(self, key, default=None):
        return self.registry.get(key, default)
    
    @property
    def module_filename(self):
        return self.filename + os.extsep + config.CACHE_EXTENSION
    
    def load(self):
        try:
            module_filename = self.module_filename
            f = open(module_filename, 'rb')
        except IOError:
            return

        try:
            try:
                self.registry = pickle.load(f)
            except EOFError:
                pass
        finally:
            f.close()
        
    def save(self):
        try:
            f = open(self.module_filename, 'wb')
        except IOError:
            return

        try:
            pickle.dump(self.registry, f, protocol=2)
        finally:
            f.close()
