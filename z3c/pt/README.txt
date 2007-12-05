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
  >>> filename = tests.__path__[0]+'/helloworld.pt'
  
  >>> template = PageTemplateFile(filename)
  >>> print template()
  <div>
     Hello World!
  </div>

Keyword-parameters are passed on to the template namespace as-is.
