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

View template classes
---------------------

View template classes are provided for templates on the file system
and for inline templates. The following symbols are defined for the
template:

  * view
  * context
  * request
  * options

Keyword-parameters are passed on to the template in a dictionary bound
to the symbol ``options``.

  >>> from z3c.pt import ViewPageTemplate, ViewPageTemplateFile
  
  >>> class ViewPageTemplateView(object):
  ...     view_page_template_file = ViewPageTemplateFile(path+'/view.pt')
  ...     view_page_template = ViewPageTemplate(open(path+'/view.pt').read())
  ...     request = u'request'
  ...     context = u'context'

  >>> view = ViewPageTemplateView()

File system:
  
  >>> print view.view_page_template_file(test=u'test')
  <div>
    <span><ViewPageTemplateView object at ...</span>
    <span>context</span>
    <span>request</span>
    <span>test</span>
  </div>

Inline:
  
  >>> print view.view_page_template(test=u'test')
  <div>
    <span><ViewPageTemplateView object at ...</span>
    <span>context</span>
    <span>request</span>
    <span>test</span>
  </div>

  
