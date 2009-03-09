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

Using 'exists:' in conjunction with a negation:

  >>> print PageTemplate("""\
  ... <div xmlns="http://www.w3.org/1999/xhtml">
  ...   <span tal:condition="not:exists:options/nope"
  ...         >I don't exist?</span>
  ... </div>""")()
  <div xmlns="http://www.w3.org/1999/xhtml">
    <span>I don't exist?</span>
  </div>

path expression with dictionaries
---------------------------------

Path expressions give preference to dictionary items instead of
dictionary attributes.

  >>> print PageTemplate("""\
  ... <div xmlns="http://www.w3.org/1999/xhtml"
  ...      tal:define="links python:{'copy':'XXX', 'delete':'YYY'}">
  ...   <span tal:content="links/copy"
  ...         >ZZZ</span>
  ... </div>""")()
  <div xmlns="http://www.w3.org/1999/xhtml">
    <span>XXX</span>
  </div>

TALES Function Namespaces
-------------------------

As described on http://wiki.zope.org/zope3/talesns.html, it is
possible to implement custom TALES Namespace Adapters. We also support
low-level TALES Function Namespaces (which the TALES Namespace
Adapters build upon).

  >>> import datetime
  >>> import zope.interface
  >>> import zope.component
  >>> from zope.traversing.interfaces import ITraversable
  >>> from zope.traversing.interfaces import IPathAdapter
  >>> from zope.tales.interfaces import ITALESFunctionNamespace
  >>> from z3c.pt.namespaces import function_namespaces

  >>> class ns1(object):
  ...     zope.interface.implements(ITALESFunctionNamespace)
  ...     def __init__(self, context):
  ...         self.context = context
  ...     def parent(self):
  ...         return self.context.parent

  >>> function_namespaces.registerFunctionNamespace('ns1', ns1)

  >>> class ns2(object):
  ...     def __init__(self, context):
  ...         self.context = context
  ...     def upper(self):
  ...         return self.context.upper()

  >>> zope.component.getGlobalSiteManager().registerAdapter(
  ...     ns2, [zope.interface.Interface], IPathAdapter, 'ns2')

  >>> class ns3(object):
  ...     def __init__(self, context):
  ...         self.context = context
  ...     def fullDateTime(self):
  ...         return self.context.strftime('%Y-%m-%d %H:%M:%S')

  >>> zope.component.getGlobalSiteManager().registerAdapter(
  ...     ns3, [zope.interface.Interface], IPathAdapter, 'ns3')


A really corner-ish case from a legacy application: the TALES
Namespace Adapter doesn't have a callable function but traverses the
remaining path instead::

  >>> from zope.traversing.interfaces import TraversalError
  
  >>> class ns4(object):
  ...     zope.interface.implements(ITraversable)
  ...
  ...     def __init__(self, context):
  ...         self.context = context
  ...
  ...     def traverse(self, name, furtherPath):
  ...         if name == 'page':
  ...             if len(furtherPath) == 1:
  ...		      pagetype = furtherPath.pop()
  ...		  elif not furtherPath:
  ...                 pagetype = 'default'
  ...             else:
  ...                 raise TraversalError("Max 1 path segment after ns4:page")
  ...             return self._page(pagetype)
  ...         if len(furtherPath) == 1:
  ...              name = '%s/%s' % (name, furtherPath.pop())
  ...         return 'traversed: ' + name
  ...
  ...     def _page(self, pagetype):
  ...         return 'called page: ' + pagetype

  >>> zope.component.getGlobalSiteManager().registerAdapter(
  ...     ns4, [zope.interface.Interface], IPathAdapter, 'ns4')

  >>> class Ob(object):
  ...     def __init__(self, title, date, parent=None, child=None):
  ...         self.title = title
  ...         self.date = date
  ...         self.parent = parent
  ...         self.child = child

  >>> child = Ob('child', datetime.datetime(2008, 12, 30, 13, 48, 0, 0))
  >>> father = Ob('father', datetime.datetime(1978, 12, 30, 13, 48, 0, 0))
  >>> grandpa = Ob('grandpa', datetime.datetime(1948, 12, 30, 13, 48, 0, 0))

  >>> child.parent = father
  >>> father.child = child
  >>> father.parent = grandpa
  >>> grandpa.child = father

  >>> class View(object):
  ...     request = u'request'
  ...     context = father
  ...
  ...     def __repr__(self):
  ...         return 'view'

  >>> view = View()
  >>> template = ViewPageTemplateFile(path+'/function_namespaces.pt')
  >>> print template.bind(view)()
  <div xmlns="http://www.w3.org/1999/xhtml">
    <span>GRANDPA</span>
    <span>2008-12-30 13:48:00</span>
    <span>traversed: link:main</span>
    <span>called page: default</span>
    <span>called page: another</span>
    <span>traversed: zope.Public</span>
    <span>traversed: text-to-html</span>
  </div>
