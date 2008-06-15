import os
import marshal
import py_compile
import struct

from imp import get_magic

MAGIC = get_magic()

def code_read(self, filename, timestamp):
    code = None
    if os.path.isfile(self.code_filename):
        fd = open(filename, 'rb')
        if fd.read(4) == MAGIC:
            ctimestamp = struct.unpack('<I', fd.read(4))[0]
            if ctimestamp == timestamp:
                code = marshal.load(fd)
        fd.close()
    return code

def code_write(self, source, filename, timestamp):
    try:
        fd = open(filename, 'wb')
        try:
            code = compile(source, filename, "exec")
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
