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
  <div xmlns="http://www.w3.org/1999/xhtml">
    Hello World!
  </div>

The ``PageTemplateFile`` class is initialized with an absolute
path to a template file on disk.

  >>> from z3c.pt import tests
  >>> path = tests.__path__[0]
  >>> template_file = PageTemplateFile(path+'/helloworld.pt')
  >>> print template_file()
  <div xmlns="http://www.w3.org/1999/xhtml">
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
  <div xmlns="http://www.w3.org/1999/xhtml">
    Hello World!
  </div>

  >>> print instance.template_file()
  <div xmlns="http://www.w3.org/1999/xhtml">
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
  <div xmlns="http://www.w3.org/1999/xhtml">
    <span>view</span>
    <span>context</span>
    <span>request</span>
    <span>test</span>
  </div>

The exercise is similar for the file-based variant.

  >>> template = ViewPageTemplateFile(path+'/view.pt')
  >>> print template.bind(view)(test=u'test')
  <div xmlns="http://www.w3.org/1999/xhtml">
    <span>view</span>
    <span>context</span>
    <span>request</span>
    <span>test</span>
  </div>

For compatibility reasons, view templates may be called with an
alternative context and request.

  >>> print template(view, u"alt_context", "alt_request", test=u'test')
  <div xmlns="http://www.w3.org/1999/xhtml">
    <span>view</span>
    <span>alt_context</span>
    <span>alt_request</span>
    <span>test</span>
  </div>

Dollar-Interpolation
--------------------

As ``z3c.pt` **should** be as compatible as possible to it's original,
we don't allow $-interpolation like in ``chameleon.zpt``::

  >>> template = PageTemplate("""\
  ... <div xmlns="http://www.w3.org/1999/xhtml">
  ...   ${this does not break}
  ... </div>""")

  >>> print template()
  <div xmlns="http://www.w3.org/1999/xhtml">
    ${this does not break}
  </div>

But we can **enable** this in a template::

  >>> template = PageTemplate("""\
  ... <div xmlns="http://www.w3.org/1999/xhtml"
  ...      xmlns:meta="http://xml.zope.org/namespaces/meta">
  ...   <div meta:interpolation="true">
  ...     ${options/foo}
  ...   </div>
  ... </div>""")

  >>> print template(foo=u'bar')
  <div xmlns="http://www.w3.org/1999/xhtml">
    <div>
      bar
    </div>
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


Global 'path' Function
----------------------

Just like ``zope.pagetemplate``, it is possible to use a globally
defined ``path()`` function in a ``python:`` expression in ``z3c.pt``:

  >>> template = PageTemplate("""\
  ... <div xmlns="http://www.w3.org/1999/xhtml">
  ...   <span tal:content="options/test" />
  ...   <span tal:content="python: path('options/test')" />
  ... </div>""")

  >>> print template(test='test')
  <div xmlns="http://www.w3.org/1999/xhtml">
    <span>test</span>
    <span>test</span>
  </div>

Global 'exists' Function
------------------------

The same applies to the ``exists()`` function:

  >>> template = PageTemplate("""\
  ... <div xmlns="http://www.w3.org/1999/xhtml">
  ...   <span tal:content="python: exists('options/test') and 'Yes' or 'No'" />
  ... </div>""")

  >>> print template(test='test')
  <div xmlns="http://www.w3.org/1999/xhtml">
    <span>Yes</span>
  </div>

'default' and path expressions
------------------------------

Another feature from standard ZPT: using 'default' means whatever the
the literal HTML contains will be output if the condition is not met.

This works for attributes:

  >>> template = PageTemplate("""\
  ... <div xmlns="http://www.w3.org/1999/xhtml">
  ...   <span tal:attributes="class options/not-existing | default"
  ...         class="blue">i'm blue</span>
  ... </div>""")

  >>> print template()
  <div xmlns="http://www.w3.org/1999/xhtml">
    <span class="blue">i'm blue</span>
  </div>

And also for contents:

  >>> template = PageTemplate("""\
  ... <div xmlns="http://www.w3.org/1999/xhtml">
  ...   <span tal:content="options/not-existing | default"
  ...         >default content</span>
  ... </div>""")

  >>> print template()
  <div xmlns="http://www.w3.org/1999/xhtml">
    <span>default content</span>
  </div>

'exists'-type expression
------------------------

Using 'exists()' function on non-global name and global name:

  >>> template = PageTemplate("""\
  ... <div xmlns="http://www.w3.org/1999/xhtml">
  ...   <span tal:content="python: exists('options/nope') and 'Yes' or 'No'"
  ...         >do I exist?</span>
  ...   <span tal:content="python: exists('nope') and 'Yes' or 'No'"
  ...         >do I exist?</span>
  ... </div>""")

  >>> print template()
  <div xmlns="http://www.w3.org/1999/xhtml">
    <span>No</span>
    <span>No</span>
  </div>

Using 'exists:' expression on non-global name and global name

  >>> template = PageTemplate("""\
  ... <div xmlns="http://www.w3.org/1999/xhtml">
  ...   <span tal:define="yup exists:options/nope" 
  ...         tal:content="python: yup and 'Yes' or 'No'"
  ...         >do I exist?</span>
  ...   <span tal:define="yup exists:nope" 
  ...         tal:content="python: yup and 'Yes' or 'No'"
  ...         >do I exist?</span>
  ... </div>""")

  >>> print template()
  <div xmlns="http://www.w3.org/1999/xhtml">
    <span>No</span>
    <span>No</span>
  </div>
