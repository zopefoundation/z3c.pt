import unittest

import zope.component.testing
import zope.configuration.xmlconfig


class TestPageTemplateFile(unittest.TestCase):
    def setUp(self):
        import z3c.pt
        zope.component.testing.setUp(self)
        zope.configuration.xmlconfig.XMLConfig('configure.zcml', z3c.pt)()

    def tearDown(self):
        zope.component.testing.tearDown(self)

    def test_nocall(self):
        from z3c.pt.pagetemplate import PageTemplateFile
        template = PageTemplateFile("nocall.pt")
        def dont_call():
            raise RuntimeError()
        result = template(callable=dont_call)
        self.failUnless(repr(dont_call) in result)

    def test_exists(self):
        from z3c.pt.pagetemplate import PageTemplateFile
        template = PageTemplateFile("exists.pt")
        def dont_call():
            raise RuntimeError()
        result = template(callable=dont_call)
        self.failUnless('ok' in result)

    def test_false(self):
        from z3c.pt.pagetemplate import PageTemplateFile
        template = PageTemplateFile("false.pt")
        result = template()
        self.failUnless('False' in result)

    def test_path(self):
        from z3c.pt.pagetemplate import PageTemplateFile
        template = PageTemplateFile("path.pt")

        class Context(object):
            dummy_wysiwyg_support = True

        context = Context()
        template = template.__get__(context, Context)

        result = template(editor="dummy")
        self.failUnless("supported" in result)
        self.failUnless("some path" in result)

def test_suite():
    import sys
    return unittest.findTestCases(sys.modules[__name__])
