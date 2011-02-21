import doctest
import unittest

OPTIONFLAGS = (doctest.ELLIPSIS |
               doctest.NORMALIZE_WHITESPACE)

import zope.component.testing
import zope.configuration.xmlconfig
import z3c.pt


def setUp(suite):
    zope.component.testing.setUp(suite)
    zope.configuration.xmlconfig.XMLConfig('configure.zcml', z3c.pt)()


def test_suite():
    filesuites = 'README.txt',
    testsuites = 'z3c.pt.expressions', 'z3c.pt.namespaces'

    return unittest.TestSuite(
        [doctest.DocFileSuite(
        filesuite, optionflags=OPTIONFLAGS,
        setUp=setUp, tearDown=zope.component.testing.tearDown,
        package="z3c.pt") for filesuite in filesuites] + \

        [doctest.DocTestSuite(
        testsuite, optionflags=OPTIONFLAGS,
        setUp=setUp, tearDown=zope.component.testing.tearDown) \
         for testsuite in testsuites]

        )

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
