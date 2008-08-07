z3c.pt
======

This document demonstrates the high-level API of the package including
error handling.


Overview
--------

Two types of TAL page template classes are provided:

``PageTemplate``, ``PageTemplateFile``
       These classes allow passing of arguments directly to the
       template namespace.

``ViewPageTemplate``, ``ViewPageTemplateFile``
       These classes should be initialized as properties in a
       view class and provide a set of default arguments to the
       template.

Templates structured as plain text are supported:

``TextTemplate``, ``TextTemplateFile``
       These classes work like their page template counterparts,
       except they work with plain text documents, extending
       to CSS stylesheets, javascript files and other non-XML
       document. Only expression interpolation is supported.

``ViewTextTemplate``, ``ViewTextTemplateFile``
       See above.

       
Page template classes
---------------------

Initialized with a string:

  >>> from z3c.pt import PageTemplate
  >>> template = PageTemplate("""\
  ... <div xmlns="http://www.w3.org/1999/xhtml"
  ...      xmlns:tal="http://xml.zope.org/namespaces/tal"
  ...      xmlns:py="http://genshi.edgewall.org">
  ...   <py:match path="xmlns:greeting">Hello ${select('@name')[0]}!</py:match>
  ...   <greeting name="World" />
  ... </div>
  ... """)

  >>> print template()
  <div>
    Hello World!
  <BLANKLINE>
  </div>

Providing the path to a template file:

  >>> from z3c.pt import PageTemplateFile
  >>> from z3c.pt import tests
  >>> path = tests.__path__[0]
  >>> template = PageTemplateFile(path+'/helloworld.pt')
  >>> print template()
  <div>
    Hello World!
  <BLANKLINE>
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
    <span>&lt;ViewPageTemplateView object at ...&gt;</span>
    <span>context</span>
    <span>request</span>
    <span>test</span>
  </div>

Inline:
  
  >>> print view.view_page_template(test=u'test')
  <div>
    <span>&lt;ViewPageTemplateView object at ...&gt;</span>
    <span>context</span>
    <span>request</span>
    <span>test</span>
  </div>

  
Text template classes
---------------------

  >>> from z3c.pt import ViewTextTemplate, ViewTextTemplateFile
  
  >>> class ViewTextTemplateView(object):
  ...     view_text_template_file = ViewTextTemplateFile(path+'/view.css')
  ...     view_text_template = ViewTextTemplate(open(path+'/view.css').read())
  ...     request = u'request'
  ...     context = u'context'

  >>> view = ViewTextTemplateView()

  >>> print view.view_text_template_file(color=u'#ccc')
  #region {
      background: #ccc;
  }

  >>> print view.view_text_template(color=u'#ccc')
  #region {
      background: #ccc;
  }


Error handling
--------------

When an exception is raised which does not expose a bug in the TAL
translation machinery, we expect the exception to contain the part of
the template source that caused the exception.

Exception while evaluating expression:

  >>> from z3c.pt import PageTemplate
  >>> PageTemplate("""\
  ... <div xmlns="http://www.w3.org/1999/xhtml"
  ...      xmlns:tal="http://xml.zope.org/namespaces/tal">
  ...   <span tal:content="range()" />
  ... </div>""").render()
  Traceback (most recent call last):
    ...
  TypeError: range expected at least 1 arguments, got 0

Exception while evaluating definition:

  >>> from z3c.pt import PageTemplate
  >>> PageTemplate("""\
  ... <div xmlns="http://www.w3.org/1999/xhtml"
  ...      xmlns:tal="http://xml.zope.org/namespaces/tal">
  ...   <span tal:define="dummy range()" />
  ... </div>""").render()
  Traceback (most recent call last):
    ...
  TypeError: range expected at least 1 arguments, got 0

Exception while evaluating interpolation:

  >>> from z3c.pt import PageTemplate
  >>> PageTemplate("""\
  ... <div xmlns="http://www.w3.org/1999/xhtml"
  ...      xmlns:tal="http://xml.zope.org/namespaces/tal">
  ...   <span>${range()}</span>
  ... </div>""").render()
  Traceback (most recent call last):
    ...
  TypeError: range expected at least 1 arguments, got 0
