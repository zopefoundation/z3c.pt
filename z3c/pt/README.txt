z3c.pt
======

Usage
-----

From a string:

  >>> from z3c.pt import PageTemplate
  >>> template = PageTemplate("""\
  ... <div xmlns="http://www.w3.org/1999/xhtml"
  ...      xmlns:tal="http://xml.zope.org/namespaces/tal/python">
  ...   Hello World!
  ... </div>
  ... """)

  >>> print template()
  <div>
     Hello World!
  </div>

From a file:

  >>> from z3c.pt import PageTemplateFile
  >>> from z3c.pt import tests
  >>> path = tests.__path__[0]
  >>> template = PageTemplateFile(path+'/helloworld.pt')
  >>> print template()
  <div>
     Hello World!
  </div>

Keyword-parameters are passed on to the template namespace as-is.

From a view:

  >>> from z3c.pt import ViewPageTemplateFile
  >>> class MockView(object):
  ...     template = ViewPageTemplateFile(path+'/view.pt')
  ...
  ...     def __init__(self):
  ...         self.request = u'my request'
  ...         self.context = u'my context'

  >>> view = MockView()
  >>> print view.template(test=u'my test')
  <div>
    <span><MockView object at ...</span>
    <span>my context</span>
    <span>my request</span>
    <span>my test</span>
  </div>
