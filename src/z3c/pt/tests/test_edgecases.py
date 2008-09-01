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

class TestUnicodeAttributeLiteral(unittest.TestCase, PlacelessSetup):
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
        <div id="${foo}"/>
        </html>
        """
        expected = """\
        <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
        "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
        <html>
        <div id="\xc2\xa9"/>
        </html>"""
        t = PageTemplate(body)
        c = unicode('\xc2\xa9', 'utf-8')
        self.assertEqual(norm(t.render(foo=c)), norm(expected))

    def test_torture(self):
        import z3c.pt
        from z3c.pt.genshi import GenshiParser
        from zope.configuration import xmlconfig
        xmlconfig.file('configure.zcml', z3c.pt)
        from z3c.pt.pagetemplate import PageTemplate
        body = """\
        <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
        "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
        <html xmlns="http://www.w3.org/1999/xhtml"
        xmlns:py="http://genshi.edgewall.org/">
        <title>\xc2\xa9</title>
        <div id="${foo}" py:attrs="dict(label=foo)"/>
        </html>
        """
        expected = """\
        <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
        "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
        <html>
        <title>\xc2\xa9</title>
        <div label="\xc2\xa9" id="\xc2\xa9"/>
        </html>"""
        t = PageTemplate(body, parser=GenshiParser())
        c = unicode('\xc2\xa9', 'utf-8')
        self.assertEqual(norm(t.render(foo=c)), norm(expected))

class TestZCMLActionsPickleable(unittest.TestCase, PlacelessSetup):
    # see also
    # http://groups.google.com/group/z3c_pt/browse_thread/thread/bd0cc94b5fd40ae0?hl=en
    def setUp(self):
        PlacelessSetup.setUp(self)

    def tearDown(self):
        PlacelessSetup.tearDown(self)
            
    def test_registry_actions_can_be_pickled_and_unpickled(self):
        from z3c import pt as package
        from zope.configuration import config
        from zope.configuration import xmlconfig
        context = config.ConfigurationMachine()
        xmlconfig.registerCommonDirectives(context)
        context.package = package
        xmlconfig.include(context, 'configure.zcml', package)
        context.execute_actions(clear=False)
        actions = context.actions
        import pickle
        dumped = pickle.dumps(actions, -1)
        new = pickle.loads(dumped)
        self.assertEqual(len(actions), len(new))

class TestExplicitDoctypes(unittest.TestCase, PlacelessSetup):
    def setUp(self):
        PlacelessSetup.setUp(self)

    def tearDown(self):
        PlacelessSetup.tearDown(self)

    def test_doctype_declared_in_constructor_adds_doctype(self):
        import z3c.pt
        from zope.configuration import xmlconfig
        xmlconfig.file('configure.zcml', z3c.pt)
        from z3c.pt.pagetemplate import PageTemplate
        from z3c.pt import doctypes
        body = """\
        <html xmlns="http://www.w3.org/1999/xhtml">
        </html>
        """
        expected = """\
        <!DOCTYPE html PUBLIC"-//W3C//DTD XHTML 1.0 Strict//EN"
        "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
        <html>
        </html>"""
        t = PageTemplate(body, doctype=doctypes.xhtml_strict)
        self.assertEqual(norm(t.render()), norm(expected))

    def test_doctype_declared_in_constructor_overrides_template_doctype(self):
        import z3c.pt
        from zope.configuration import xmlconfig
        xmlconfig.file('configure.zcml', z3c.pt)
        from z3c.pt.pagetemplate import PageTemplate
        from z3c.pt import doctypes
        body = """\
        <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
        "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
        <html xmlns="http://www.w3.org/1999/xhtml">
        </html>
        """
        expected = """\
        <!DOCTYPE html PUBLIC"-//W3C//DTD XHTML 1.0 Strict//EN"
        "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
        <html>
        </html>"""
        t = PageTemplate(body, doctype=doctypes.xhtml_strict)
        self.assertEqual(norm(t.render()), norm(expected))

    def test_doctype_assigned_to_instance_overrides_constructor_doctype(self):
        import z3c.pt
        from zope.configuration import xmlconfig
        xmlconfig.file('configure.zcml', z3c.pt)
        from z3c.pt.pagetemplate import PageTemplate
        from z3c.pt import doctypes
        body = """\
        <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
        "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
        <html xmlns="http://www.w3.org/1999/xhtml">
        </html>
        """
        expected = """\
        <!DOCTYPE HTML PUBLIC"-//W3C//DTD HTML4.01 Transitional//EN"
        "http://www.w3.org/TR/html4/loose.dtd">
        <html>
        </html>"""
        t = PageTemplate(body, doctype=doctypes.xhtml_strict)
        t.doctype = doctypes.html
        self.assertEqual(norm(t.render()), norm(expected))

class TestBadAttributeInterpolationWithTAL(unittest.TestCase, PlacelessSetup):
    def test_snippet(self):
        body = """\
        <div xmlns:tal="http://xml.zope.org/namespaces/tal"
             xmlns="http://www.w3.org/1999/xhtml">
        <span tal:repeat="ltr letters">
	<a class="${ltr.iscurrent}" href="${ltr.href}">${ltr.letter}</a>
        </span>
        </div>
        """
        import z3c.pt
        from zope.configuration import xmlconfig
        xmlconfig.file('configure.zcml', z3c.pt)
        from z3c.pt.pagetemplate import PageTemplate
        letters = [
            {'letter':'A', 'href':'?titlestartswith=A',
             'iscurrent':'current'},
            {'letter':'B', 'href':'?titlestartswith=B',
             'iscurrent':'notcurrent'},
            ]
        t = PageTemplate(body)
        expected = """\
        <div>
        <span>
	<a class="current" href="?titlestartswith=A">A</a>
        </span>
        <span>
	<a class="notcurrent" href="?titlestartswith=B">B</a>
        </span>
        </div>"""

        output = t.render(letters=letters)
        
        self.assertEqual(norm(output), norm(expected))
        

def norm(s):
    return s.replace(' ', '').replace('\n', '')

def test_suite():
    import sys
    return unittest.findTestCases(sys.modules[__name__])
