import unittest

class TestGenerator(unittest.TestCase):
    def test_generator_returns_utf_8_encoded_text(self):
        from z3c.pt.generation import Generator
        gen = Generator([])
        from StringIO import StringIO
        gen.stream = StringIO(u'<div>\xc2\xa9</div>')
        code, ns = gen()
        self.failUnless(isinstance(code, str), repr(code))

def test_suite():
    import sys
    return unittest.findTestCases(sys.modules[__name__])
