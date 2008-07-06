import os
import marshal
import py_compile
import struct

from imp import get_magic
from sha import sha
from UserDict import UserDict

from z3c.pt.config import FILECACHE

MAGIC = get_magic()

def code_read(filename, timestamp):
    code = None
    if os.path.isfile(filename):
        fd = open(filename, 'rb')
        if fd.read(4) == MAGIC:
            ctimestamp = struct.unpack('<I', fd.read(4))[0]
            if ctimestamp == timestamp:
                code = marshal.load(fd)
        fd.close()
    return code

def code_write(code, filename, timestamp):
    try:
        fd = open(filename, 'wb')
        try:
            # Create a byte code file. See the py_compile module
            fd.write('\0\0\0\0')
            fd.write(struct.pack("<I", timestamp))
            marshal.dump(code, fd)
            fd.flush()
            fd.seek(0, 0)
            fd.write(MAGIC)
        finally:
            fd.close()
        py_compile.set_creator_type(filename)
    except (IOError, OSError):
        pass

class CachingDict(UserDict):

    def __init__(self, filename, mtime, pagetemplate):
        UserDict.__init__(self)

        if FILECACHE:
            # Update ourselves with the values from the cache file
            filename = sha(filename).hexdigest()
            self.cachedir = os.path.join(FILECACHE, filename)
            self.mtime = mtime

            if os.path.isdir(self.cachedir):
                for cachefile in os.listdir(self.cachedir):
                    value = None
                    cachepath = os.path.join(self.cachedir, cachefile)
                    code = code_read(cachepath, self.mtime)
                    if code is not None:
                        self[int(cachefile)] = pagetemplate.execute(code)
                        pagetemplate._v_last_read = mtime

    # If we don't have a file cache, behave like a normal instance level dict
    if FILECACHE:
        def store(self, params, code):
            key = hash(''.join(params))
            if not os.path.isdir(self.cachedir):
                os.mkdir(self.cachedir)

            cachefile = os.path.join(self.cachedir, str(key))
            code_write(code, cachefile, self.mtime)
