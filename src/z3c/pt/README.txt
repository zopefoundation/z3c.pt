z3c.pt
======

This section demonstrates the high-level template classes. All page
template classes in ``z3c.pt`` use path-expressions by default.

Page templates
--------------

  >>> from z3c.pt.pagetemplate import PageTemplate
  >>> from z3c.pt.pagetemplate import PageTemplateFile

The ``PageTemplate`` class is initialized with a string.

  >>> template = PageTemplate("""\
  ... <div xmlns="http://www.w3.org/1999/xhtml">
  ...   Hello World!
  ... </div>""")

  >>> print template()
  <div>
    Hello World!
  </div>

The ``PageTemplateFile`` class is initialized with an absolute
path to a template file on disk.

  >>> from z3c.pt import tests
  >>> path = tests.__path__[0]
  >>> template_file = PageTemplateFile(path+'/helloworld.pt')
  >>> print template_file()
  <div>
    Hello World!
  </div>

  >>> import os
  >>> template_file.filename.startswith(os.sep)
  True

Both may be used as class attributes (properties).

  >>> class MyClass(object):
  ...     template = PageTemplate("""\
  ...       <div xmlns="http://www.w3.org/1999/xhtml">
  ...          Hello World!
  ...       </div>""")
  ...
  ...     template_file = PageTemplateFile(path+'/helloworld.pt')

  >>> instance = MyClass()
  >>> print instance.template()
  <div>
    Hello World!
  </div>

  >>> print instance.template_file()
  <div>
    Hello World!
  </div>

View page templates
-------------------

  >>> from z3c.pt.pagetemplate import ViewPageTemplate
  >>> from z3c.pt.pagetemplate import ViewPageTemplateFile

  >>> class View(object):
  ...     request = u'request'
  ...     context = u'context'
  ...
  ...     def __repr__(self):
  ...         return 'view'

  >>> view = View()

As before, we can initialize view page templates with a string (here
incidentally loaded from disk).

  >>> template = ViewPageTemplate(
  ...     open(path+'/view.pt').read())

To render the template in the context of a view, we bind the template
passing the view as an argument (view page templates derive from the
``property``-class and are usually defined as an attribute on a view
class).

  >>> print template.bind(view)(test=u'test')
  <div>
    <span>view</span>
    <span>context</span>
    <span>request</span>
    <span>test</span>
  </div>

The exercise is similar for the file-based variant.

  >>> template = ViewPageTemplateFile(path+'/view.pt')
  >>> print template.bind(view)(test=u'test')
  <div>
    <span>view</span>
    <span>context</span>
    <span>request</span>
    <span>test</span>
  </div>

Text templates
--------------

  >>> from z3c.pt.texttemplate import ViewTextTemplate
  >>> from z3c.pt.texttemplate import ViewTextTemplateFile

  >>> template = ViewTextTemplate(open(path+'/view.css').read())
  >>> print template.bind(view)(color=u'#ccc')
  #region {
      background: #ccc;
  }

  >>> template = ViewTextTemplateFile(path+'/view.css')
  >>> print template.bind(view)(color=u'#ccc')
  #region {
      background: #ccc;
  }
