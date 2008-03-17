import zope.testing
import unittest

OPTIONFLAGS = (zope.testing.doctest.ELLIPSIS |
               zope.testing.doctest.NORMALIZE_WHITESPACE)

import zope.component.testing
import zope.configuration.xmlconfig

import z3c.pt

def setUp(suite):
    zope.component.testing.setUp(suite)
    zope.configuration.xmlconfig.XMLConfig('configure.zcml', z3c.pt)()

def test_suite():
    filesuites = ('README.txt', 'BENCHMARKS.txt', 'translation.txt', 'i18n.txt', 'codegen.txt')
    testsuites = ('z3c.pt.translation', 'z3c.pt.clauses', 'z3c.pt.expressions')

    return unittest.TestSuite(
        [zope.testing.doctest.DocTestSuite(
        doctest, optionflags=OPTIONFLAGS,
        setUp=setUp, tearDown=zope.component.testing.tearDown) \
         for doctest in testsuites] + 
        
        [zope.testing.doctest.DocFileSuite(
        doctest, optionflags=OPTIONFLAGS,
        setUp=setUp, tearDown=zope.component.testing.tearDown,
        package="z3c.pt") for doctest in filesuites]
        )

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
