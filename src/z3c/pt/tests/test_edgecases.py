import unittest

from zope.component.testing import PlacelessSetup

class TestNumericEntityPlusUnicodeParameterInsertedLiterally(unittest.TestCase,
                                                             PlacelessSetup):
    # See also
    # http://groups.google.com/group/z3c_pt/browse_thread/thread/aea963d25a1778d0?hl=en
    def setUp(self):
        PlacelessSetup.setUp(self)

    def tearDown(self):
        PlacelessSetup.tearDown(self)
            
    def test_it(self):
        import z3c.pt
        from zope.configuration import xmlconfig
        xmlconfig.file('configure.zcml', z3c.pt)
        from z3c.pt.pagetemplate import PageTemplate
        body = """\
        <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
        "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
        <html xmlns="http://www.w3.org/1999/xhtml">
        ${foo} &#169;
        </html>
        """
        expected = """\
        <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
        "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
        <html>
        foo \xc2\xa9
        </html>"""
        t = PageTemplate(body)
        self.assertEqual(norm(t.render(foo=u'foo')), norm(expected))

def norm(s):
    return s.replace(' ', '').replace('\n', '')

def test_suite():
    import sys
    return unittest.findTestCases(sys.modules[__name__])
