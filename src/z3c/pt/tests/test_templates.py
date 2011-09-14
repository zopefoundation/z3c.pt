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

    def test_false_attribute(self):
        from z3c.pt.pagetemplate import PageTemplateFile
        template = PageTemplateFile("false.pt")
        result = template()
        self.failUnless('False' in result)

    def test_boolean_attribute(self):
        from z3c.pt.pagetemplate import PageTemplateFile
        template = PageTemplateFile("boolean.pt")
        result = template()
        self.failIf('False' in result)
        self.failUnless('checked="checked"' in result)

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

    def test_provider(self):
        from z3c.pt.pagetemplate import ViewPageTemplateFile

        class Context(object):
            pass

        class Request(object):
            response = None

        class View(object):
            __call__ = ViewPageTemplateFile("provider.pt")

        class Provider(object):
            def __init__(self, *args):
                data.extend(list(args))

            def update(self):
                data.extend("updated")

            def render(self):
                return """<![CDATA[ %s ]]>""" % repr(data)

        view = View()
        data = []

        from zope.interface import implementedBy
        from zope.component import provideAdapter
        from zope.contentprovider.interfaces import IContentProvider

        provideAdapter(
            Provider, (
                implementedBy(Context),
                implementedBy(Request),
                implementedBy(View)
                ),
            IContentProvider,
            name="content"
            )

        result = view(context=Context(), request=Request())
        self.failUnless(repr(data) in result)


def test_suite():
    import sys
    return unittest.findTestCases(sys.modules[__name__])
