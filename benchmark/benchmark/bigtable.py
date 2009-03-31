# This test is adopted from the spifire project, which has an extensive
# test suite of different templating languages.

# You can run it via: bin/py benchmark/benchmark/bigtable.py

import sys
import timeit

from zope.pagetemplate import pagetemplate

from chameleon.zpt import template

bigtable_z3c = template.PageTemplate("""
<table xmlns="http://www.w3.org/1999/xhtml"
xmlns:tal="http://xml.zope.org/namespaces/tal">
<tr tal:repeat="row table">
<td tal:repeat="column row.values()" tal:content="column">
</td></tr></table>
""")

bigtable_zope = pagetemplate.PageTemplate()
bigtable_zope.pt_edit("""\
<table xmlns="http://www.w3.org/1999/xhtml"
xmlns:tal="http://xml.zope.org/namespaces/tal">
<tr tal:repeat="row python: options['table']">
<td tal:repeat="c python: row.values()" tal:content="c">
</td></tr></table>""", 'text/xhtml')


table = [dict(a=1,b=2,c=3,d=4,e=5,f=6,g=7,h=8,i=9,j=10) \
         for x in range(1000)]

def setup():
    import z3c.pt
    from zope.component.testing import setUp
    from zope.configuration import xmlconfig

    setUp()
    xmlconfig.XMLConfig('configure.zcml', z3c.pt)()

def test_z3c():
    """z3c.pt template"""
    data = bigtable_z3c(table=table)

def test_zope():
    """zope.pagetemplate template"""
    data = bigtable_zope(table=table)

def run(which=None, number=10):
    tests = ['test_z3c', 'test_zope']

    if which:
        tests = ['test_z3c']

    for test in tests:
        setup = 'from __main__ import setup, %s; setup(); %s()' % (test, test)

        t = timeit.Timer(setup=setup,
                         stmt='%s()' % test)
        time = t.timeit(number=number) / number

        if time < 0.00001:
            result = '   (not installed?)'
        else:
            result = '%16.2f ms' % (1000 * time)
        print '%-35s %s' % (getattr(sys.modules[__name__], test).__doc__, result)


if __name__ == '__main__':
    which = None
    if '-p' in sys.argv:
        which = True
        from cProfile import Profile
        import pstats
        profiler = Profile()
        setup()
        test_z3c()
        profiler.runcall(test_z3c)
        profiler.dump_stats('template.prof')
        stats = pstats.Stats(profiler)
        stats.strip_dirs()
        stats.sort_stats('time', 'calls')
        stats.print_stats()
    else:
        run(which, 1)
