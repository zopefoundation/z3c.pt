import os
import unittest
import time
import sys

import zope.component.testing
import zope.configuration.xmlconfig
import zope.pagetemplate.pagetemplatefile
import z3c.pt

from chameleon import zpt
from chameleon.core import config
from chameleon.core import filecache

from z3c.pt import pagetemplate

try:
    from lxml import etree
except ImportError:
    etree = None

class test_request:
    response = None

def benchmark(title):
    def decorator(f):
        def wrapper(*args):
            print "==========================\n %s\n==========================" % title
            return f(*args)
        return wrapper
    return decorator

def timing(func, *args, **kwargs):
    t1 = t2 = time.time()
    i = 0
    while t2 - t1 < 3:
        func(*args, **kwargs)
        i += 1
        t2 = time.time()
    return float(100*(t2-t1))/i

def bigtable_python_lxml(table=None):
    root = etree.Element("html")
    for r in table:
        row = root.makeelement("tr")
        for c in r.values():
            d = c + 1
            col = row.makeelement("td")
            span = col.makeelement("span")
            span.attrib['class'] = 'column-%d' % d
            span.text = str(d)
            col.append(span)
            row.append(col)
        root.append(row)
    return etree.tostring(root, encoding='utf-8')

START = 0
EMPTY = 1
END = 2
TEXT = 3

def yield_stream(table=None):
    yield START, ("html", ()), None
    for r in table:
        yield START, ("tr", ()), None
        for c in r.values():
            d = c + 1
            yield START, ("td", ()), None
            yield START, ("span", (('class', 'column-%d' % d),)), None
            if d.__class__ not in (str, unicode, int, float) and hasattr(d, '__html__'):
                raise
            yield TEXT, str(d), None
            yield END, "span", None
            yield END, "td", None
        yield END, "tr", None
    yield END, "html", None

def list_stream(table=None):
    l = []
    a = l.append
    a((START, ("html", ()), None))
    for r in table:
        a((START, ("tr", ()), None))
        for c in r.values():
            d = c + 1
            a((START, ("td", ()), None))
            a((START, ("span", (('class', 'column-%d' % d),)), None))
            if d.__class__ not in (str, unicode, int, float) and hasattr(d, '__html__'):
                raise
            a((TEXT, str(d), None))
            a((END, "span", None))
            a((END, "td", None))
        a((END, "tr", None))
    a((END, "html", None))
    return l

def bigtable_python_stream(table=None, renderer=None):
    stream = renderer(table=table)
    return "".join(stream_output(stream))

def stream_output(stream):
    for kind, data, pos in stream:
        if kind is START or kind is EMPTY:
            tag, attrib = data
            yield "<%s " % tag
            for attr, value in attrib:
                yield '%s="%s" ' % (attr, value)
            if kind is EMPTY:
                yield "/>"
        elif kind is END:
            yield "</%s" % data
        elif kind is TEXT:
            yield data

class BaseTestCase(unittest.TestCase):

    table = [dict(a=1,b=2,c=3,d=4,e=5,f=6,g=7,h=8,i=9,j=10) \
             for x in range(1000)]

    def setUp(suite):
        zope.component.testing.setUp(suite)
        zope.configuration.xmlconfig.XMLConfig('configure.zcml', z3c.pt)()

    def tearDown(suite):
        zope.component.testing.tearDown(suite)

class BenchmarkTestCase(BaseTestCase):

    helloworld_z3c = pagetemplate.PageTemplate("""\
    <div xmlns="http://www.w3.org/1999/xhtml">
    Hello World!
    </div>""")

    helloworld_zope = zope.pagetemplate.pagetemplate.PageTemplate()
    helloworld_zope.pt_edit("""\
    <div xmlns="http://www.w3.org/1999/xhtml">
    Hello World!
    </div>""", 'text/xhtml')
    
    bigtable_python_z3c = zpt.template.PageTemplate("""\
    <table xmlns="http://www.w3.org/1999/xhtml"
    xmlns:tal="http://xml.zope.org/namespaces/tal">
    <tr tal:repeat="row table">
    <td tal:repeat="c row.values()">
    <span tal:define="d c + 1"
    tal:attributes="class 'column-' + str(d)"
    tal:content="d" />
    </td>
    </tr>
    </table>""")

    bigtable_path_z3c = pagetemplate.PageTemplate("""\
    <table xmlns="http://www.w3.org/1999/xhtml"
    xmlns:tal="http://xml.zope.org/namespaces/tal"
    tal:default-expression="path">
    <tr tal:repeat="row options/table">
    <td tal:repeat="c python: row.values()">
    <span tal:define="d python: c + 1"
    tal:attributes="class string:column-${d}"
    tal:content="d" />
    </td>
    </tr>
    </table>""")

    bigtable_python_zope = zope.pagetemplate.pagetemplate.PageTemplate()
    bigtable_python_zope.pt_edit("""\
    <table xmlns="http://www.w3.org/1999/xhtml"
    xmlns:tal="http://xml.zope.org/namespaces/tal">
    <tr tal:repeat="row python: options['table']">
    <td tal:repeat="c python: row.values()">
    <span tal:define="d python: c + 1"
    tal:attributes="class python:'column-'+str(d)"
    tal:content="d" />
    </td>
    </tr>
    </table>""", 'text/xhtml')

    bigtable_path_zope = zope.pagetemplate.pagetemplate.PageTemplate()
    bigtable_path_zope.pt_edit("""\
    <table xmlns="http://www.w3.org/1999/xhtml"
    xmlns:tal="http://xml.zope.org/namespaces/tal">
    <tr tal:repeat="row options/table">
    <td tal:repeat="c row/values">
    <span tal:define="d python: c + 1"
    tal:attributes="class string:column-${d}"
    tal:content="d" />
    </td>
    </tr>
    </table>""", 'text/xhtml')

    bigtable_python_macros_z3c = pagetemplate.PageTemplate("""\
    <metal:rows
    xmlns:tal="http://xml.zope.org/namespaces/tal"
    xmlns:metal="http://xml.zope.org/namespaces/metal"
    define-macro="rows">
    <tr tal:repeat="row table">
      <td metal:define-slot="columns" />
    </tr>
    </metal:rows>""")

    bigtable_python_macro_version_z3c = pagetemplate.PageTemplate("""\
    <table xmlns="http://www.w3.org/1999/xhtml"
           xmlns:tal="http://xml.zope.org/namespaces/tal"
           xmlns:metal="http://xml.zope.org/namespaces/metal"
    tal:define="table python: options['table'];
                macros python: options['macros']">
    <tr metal:use-macro="python: macros['rows']">
    <metal:columns fill-slot="columns">
    <td tal:repeat="c python: row.values()">
    <span tal:define="d python: c + 1"
          tal:attributes="class python: 'column-' + str(d)"
          tal:content="python: d" />
    </td>
    </metal:columns>
    </tr>
    </table>""")

    bigtable_python_macros_zope = zope.pagetemplate.pagetemplate.PageTemplate()
    bigtable_python_macros_zope.pt_edit(
        bigtable_python_macros_z3c.body, 'text/xhtml')

    bigtable_python_macro_version_zope = zope.pagetemplate.pagetemplate.PageTemplate()
    bigtable_python_macro_version_zope.pt_edit(
        bigtable_python_macro_version_z3c.body, 'text/xhtml')

    @benchmark(u"Hello World")
    def testHelloWorld(self):
        t_z3c = timing(self.helloworld_z3c)
        t_zope = timing(self.helloworld_zope)

        print "z3c.pt:            %.3f" % t_z3c
        print "zope.pagetemplate: %.3f" % t_zope
        print "                   %.2fX" % (t_zope/t_z3c)

    @benchmark(u"Big table (python)")
    def testBigTablePython(self):
        table = self.table

        t_z3c = timing(self.bigtable_python_z3c, table=table)
        t_zope = timing(self.bigtable_python_zope, table=table)

        if etree:
            t_lxml = timing(bigtable_python_lxml, table=table)
        else:
            t_lxml = 0.0

        t_stream1 = timing(bigtable_python_stream, table=table, renderer=yield_stream)
        t_stream2 = timing(bigtable_python_stream, table=table, renderer=list_stream)

        print "zope.pagetemplate: %.2f" % t_zope
        if t_lxml:
            print "lxml:              %.2f" % t_lxml
        print "stream (yield)     %.2f" % t_stream1
        print "stream (list)      %.2f" % t_stream2
        print "--------------------------"
        print "z3c.pt:            %.2f" % t_z3c
        print "--------------------------"
        print "ratio to zpt:      %.2fX" % (t_zope/t_z3c)
        print "ratio to stream:   %.2fX" % (t_stream1/t_z3c)
        print "stream to zpt:     %.2fX" % (t_zope/t_stream1)
        if t_lxml:
            print "ratio to lxml:     %.2fX" % (t_lxml/t_z3c)

    @benchmark(u"Big table (path)")
    def testBigTablePath(self):
        table = self.table

        t_z3c = timing(self.bigtable_path_z3c, table=table, request=test_request)
        t_zope = timing(self.bigtable_path_zope, table=table)

        print "z3c.pt:            %.2f" % t_z3c
        print "zope.pagetemplate: %.2f" % t_zope
        print "                   %.2fX" % (t_zope/t_z3c)

    @benchmark(u"Big table (macro)")
    def testBigTableMacro(self):
        table = self.table

        t_z3c = timing(
            self.bigtable_python_macro_version_z3c,
            table=table,
            macros=self.bigtable_python_macros_z3c.macros)
        t_zope = timing(
            self.bigtable_python_macro_version_zope,
            table=table,
            macros=self.bigtable_python_macros_zope.macros)

        print "z3c.pt:            %.2f" % t_z3c
        print "zope.pagetemplate: %.2f" % t_zope
        print "--------------------------"
        print "ratio to zpt:      %.2fX" % (t_zope/t_z3c)

    @benchmark(u"Compilation")
    def testCompilation(self):
        table = self.table

        t_z3c = timing(self.bigtable_python_z3c.compiler, None, True)
        t_zope = timing(self.bigtable_python_zope._cook)

        print "z3c.pt:            %.2f" % t_z3c
        print "zope.pagetemplate: %.2f" % t_zope
        print "                   %.2fX" % (t_zope/t_z3c)

class FileBenchmarkTestCase(BaseTestCase):

    def setUp(self):
        BaseTestCase.setUp(self)
        self.files = os.path.abspath(os.path.join(__file__, '..', 'input'))
        self.cache = os.path.abspath(os.path.join(__file__, '..', '..', '..', 'cache'))

    def _testfile(self, name):
        return os.path.join(self.files, name)

    @benchmark(u"Compilation (Cached)")
    def testCache(self):
        table = self.table

        z3cfile = zpt.template.PageTemplateFile(
            self._testfile('bigtable_python_z3c.pt'))
        z3cfile.registry = filecache.TemplateCache(z3cfile.filename, 1)
        z3cfile.registry.purge()
        
        zopefile = zope.pagetemplate.pagetemplatefile.PageTemplateFile(
            self._testfile('bigtable_python_zope.pt'))

        # make sure both templates are fully prepared
        len(zopefile(table=table))
        len(z3cfile(table=table))

        # save registry
        assert len(z3cfile.registry) == 1
        
        t_cached_z3c = timing(z3cfile.registry.load)
        t_cook_z3c = timing(z3cfile.compiler, None, True)
        t_zope = timing(zopefile._cook)
                
        print "z3c.pt cooking:    %.3f" % t_cook_z3c
        print "--------------------------"
        print "z3c.pt cached:     %.3f" % t_cached_z3c
        print "zope.pagetemplate: %.3f" % t_zope
        print "ratio to zpt:      %.2fX" % (t_zope/t_cached_z3c)

    @benchmark(u"Big table (python) File")
    def testBigTablePythonFile(self):
        table = self.table

        z3cfile = zpt.template.PageTemplateFile(
            self._testfile('bigtable_python_z3c.pt'))

        zopefile = zope.pagetemplate.pagetemplatefile.PageTemplateFile(
            self._testfile('bigtable_python_zope.pt'))

        t_z3c = timing(z3cfile.render, table=table)
        t_zope = timing(zopefile, table=table)

        print "z3c.pt:            %.2f" % t_z3c
        print "zope.pagetemplate: %.2f" % t_zope
        print "                   %.2fX" % (t_zope/t_z3c)

    @benchmark(u"Big table (path) File")
    def testBigTablePathFile(self):
        table = self.table

        z3cfile = pagetemplate.PageTemplateFile(
            self._testfile('bigtable_path_z3c.pt'))

        zopefile = zope.pagetemplate.pagetemplatefile.PageTemplateFile(
            self._testfile('bigtable_path_zope.pt'))

        t_z3c = timing(z3cfile.render, table=table, request=test_request)
        t_zope = timing(zopefile, table=table, request=test_request)

        print "z3c.pt:            %.2f" % t_z3c
        print "zope.pagetemplate: %.2f" % t_zope
        print "                   %.2fX" % (t_zope/t_z3c)

# Use a custom context to add real i18n lookup

from zope.i18n import translate
from zope.i18n.interfaces import INegotiator
from zope.i18n.interfaces import ITranslationDomain
from zope.i18n.negotiator import Negotiator
from zope.i18n.simpletranslationdomain import SimpleTranslationDomain
from zope.i18n.tests.test_negotiator import Env
from zope.tales.tales import Context

class ZopeI18NContext(Context):

    def translate(self, msgid, domain=None, context=None,
                  mapping=None, default=None):
        context = self.vars['options']['env']
        return translate(msgid, domain, mapping,
                         context=context, default=default)

def _getContext(self, contexts=None, **kwcontexts):
    if contexts is not None:
        if kwcontexts:
            kwcontexts.update(contexts)
        else:
            kwcontexts = contexts
    return ZopeI18NContext(self, kwcontexts)

def _pt_getEngineContext(namespace):
    self = namespace['template']
    engine = self.pt_getEngine()
    return _getContext(engine, namespace)


class I18NBenchmarkTestCase(BaseTestCase):

    def setUp(self):
        BaseTestCase.setUp(self)
        self.env = Env(('da', 'en', 'fr', 'no'))
        zope.component.provideUtility(Negotiator(), INegotiator)
        catalog = SimpleTranslationDomain('domain')
        zope.component.provideUtility(catalog, ITranslationDomain, 'domain')
        self.files = os.path.abspath(os.path.join(__file__, '..', 'input'))

    def tearDown(self):
        BaseTestCase.tearDown(self)

    def _testfile(self, name):
        return os.path.join(self.files, name)

    @benchmark(u"Internationalization")
    def testI18N(self):
        table = self.table

        z3cfile = pagetemplate.PageTemplateFile(
            self._testfile('bigtable_i18n_z3c.pt'))

        zopefile = zope.pagetemplate.pagetemplatefile.PageTemplateFile(
            self._testfile('bigtable_i18n_zope.pt'))

        # In order to have a fair comparision, we need real zope.i18n handling
        zopefile.pt_getEngineContext = _pt_getEngineContext

        assert config.SYMBOLS.i18n_context=='_i18n_context'
        
        t_z3c = timing(z3cfile, table=table, target_language='klingon')
        t_zope = timing(zopefile, table=table, env=self.env)

        print "z3c.pt:            %.2f" % t_z3c
        print "zope.pagetemplate: %.2f" % t_zope
        print "                   %.2fX" % (t_zope/t_z3c)

    @benchmark(u"I18N (disabled)")
    def testDisabledI18N(self):
        table = self.table

        z3cfile = pagetemplate.PageTemplateFile(
            self._testfile('bigtable_i18n_z3c.pt'))

        zopefile = zope.pagetemplate.pagetemplatefile.PageTemplateFile(
            self._testfile('bigtable_i18n_zope.pt'))

        zopefile.pt_getEngineContext = _pt_getEngineContext

        t_z3c = timing(z3cfile, table=table)
        t_zope = timing(zopefile, table=table, env=self.env)

        print "z3c.pt:            %.2f" % t_z3c
        print "zope.pagetemplate: %.2f" % t_zope
        print "                   %.2fX" % (t_zope/t_z3c)

def test_suite():
    config.DISK_CACHE = False
    
    return unittest.TestSuite((
        unittest.makeSuite(BenchmarkTestCase),
        unittest.makeSuite(FileBenchmarkTestCase),
        unittest.makeSuite(I18NBenchmarkTestCase),
        ))

if __name__ == "__main__":
    unittest.main(defaultTest="test_suite")

