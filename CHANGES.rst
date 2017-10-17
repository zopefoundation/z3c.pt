===========
 Changelog
===========

3.1.0 (unreleased)
===================

- Add support for Python 3.6.
- Drop support for Python 3.3.
- Use the adapter namespace from ``zope.pagetemplate`` if it's
  available, instead of the backwards compatibility shim in
  ``zope.app.pagetemplate``. See `issue 3
  <https://github.com/zopefoundation/z3c.pt/issues/3>`_.
- Add the ``string`` and ``nocall`` functions for use inside Python
  expressions. See `issue 2
  <https://github.com/zopefoundation/z3c.pt/issues/2>`_.


3.0 (2016-09-02)
================

- Added support for Python 3.4, 3.5, PyPy and PyPy3.

- Dropped support for Python 2.6.


3.0.0a1 (2013-02-25)
====================

Compatibility:

- Added support for Python 3.3.

- Added a small patch to ``chameleon.i18n`` to define ``basestring``.

Bugfixes:

- Allow segments of path expressions to start with a digit.


2.2.3 (2012-06-01)
==================

Compatibility:

- The translation function now accepts (but ignores) a ``context``
  argument. This fixes a compatibility issue with Chameleon 2.9.x.

2.2.2 (2012-04-24)
==================

Bugfixes:

- Do not rely on the "LANGUAGE" request key to skip language
  negotiation. Instead, we assume that negotiation is cheap (and
  probably cached).

2.2.1 (2012-02-15)
==================

- Only require Chameleon >= 2.4, was needlessly bumped in last release.

- Add test extra, remove versions from buildout.cfg.


2.2 (2012-01-08)
================

Features:

- Whitespace between attributes is now reduced to a single whitespace
  character.

- The ``request`` symbol is no longer required to evaluate a path
  expression; it now defaults to ``None`` if not present in the
  namespace.

Bugfixes:

- The content provider expression now correctly applies TAL namespace
  data.

Changes:

- The ``ZopeTraverser`` class has been removed and replaced with a
  simple function.

2.1.5 (2011-11-24)
==================

- Use non-strict mode if available for compatibility with the
  reference engine where expressions are only compiled at evaluation
  time.

2.1.4 (2011-09-14)
==================

- The provider expression is now first evaluated as a string
  expression, the result of which is used as the content provider
  name.

  This fixes an issue where (provider-) string expressions would not
  get evaluated correctly, e.g. ``provider: ${mgr}``.

2.1.3 (2011-08-22)
==================

- Configure HTML boolean attributes (in HTML-mode only)::

      "compact", "nowrap", "ismap", "declare", "noshade",
      "checked", "disabled", "readonly", "multiple", "selected",
      "noresize", "defer"

2.1.2 (2011-08-19)
==================

- Enable option ``literal_false`` to get the behavior that a value of
  ``False`` does not drop an attribute.

2.1.1 (2011-08-11)
==================

- Make sure the builtin names 'path' and 'exists' can be redefined.

- Guard ``sys.modules`` (mapped to the builtin variable "modules")
  against import-time side effects using ``ProxyFactory``.

2.1 (2011-07-28)
================

- Use dynamic expression evaluation framework that comes included with
  Chameleon.

2.0 (2011-07-14)
================

- Point release.

- Move implementation-specific context setup to ``render``
  method. This allows use of template class with an already prepared
  context.

- Fixed issue with the call flag on the Zope traverser compiler.

2.0-rc3 (2011-07-11)
====================

- Python-expressions are no longer TALES-expressions; previously, the
  pipe operator would split Python expression clauses, allowing
  fallbacks even for Python expressions, but this is not the standard
  behavior of ZPT.

- Fixed an issue where an error which occurred inside a dynamic
  ``path`` or ``exists`` evaluation would fail to propagate due to a
  missing remote context.

- Set variables ``here`` and ``context`` to the bound instance value
  on ``PageTemplate`` instances.

2.0-rc2 (2011-03-24)
====================

- Fixed an issue with ``"exists:"`` expression where a callable would
  be attempted called. It is meanwhile implied with this expression
  types that it should use the ``"nocall:"`` pragma.


2.0-rc1 (2011-02-28)
====================

- Update to Chameleon 2.0.

  This release includes many changes and is a complete rewrite of the
  1.x series.

  Platform:

  * Python 2.5+ now required.

  Notable changes:

  * Expression interpolation is always enabled.

  * Whitespace output is different, now closely aligned to the
    template input.

  * New language constructs:

    1) tal:on-error
    2) tal:switch
    3) tal:case

  Incompatibilities:

  * The expression translation interface has been replaced with an
    expression engine. This means that all expressions must be
    rewritten.

- The exists expression evaluator should ignore KeyError exceptions
  as well.

- Special-case handling of Zope2's Missing.MV as used by
  Products.ZCatalog for LP#649343.
  [rossp]

1.2.1 (2010/05/13)
------------------

- Bind template to the template object in the general case.

1.2 (2010/05/12)
----------------

- Fixed compatibility issue with recent change in Chameleon.

- Fixed regression introduced with ``args`` being passed
  in. Incidentally, the name ``args`` was used as the star argument
  name.

- Look at language set on request before invoking the zope.i18n
  negotiator. This makes i18n work again on Zope2.

1.1.1 (2010/04/06)
------------------

- Fixed issue where arguments were not passed on to template as
  ``args``.

1.1.0 (2010/01/09)
------------------

- Update to combined Chameleon distribution.

1.0.1 (2009/07/06)
------------------

- Bind translation context (request) to translation method. Although
  not required in newer versions of the translation machinery, some
  versions will ask for a translation context in order to negotiate
  language even when a language is explicitly passed in.

- Declare zope security settings for classes when zope.security is present
  as the "class" ZCML directive was moved there.

1.0.0 (2009/07/06)
------------------

- First point release.

1.0b17 (2009/06/14)
-------------------

- Made the Zope security declaration for the repeat dictionary be conditional
  on the presence of zope.app.security instead of zope.app.component.

1.0b16 (2009/05/20)
-------------------

- Updated run-time expression evaluator method to work after a recent
  architectural change in Chameleon. [malthe]

- Check that we have a non-trivial response-object before trying to
  set the content type. [malthe]

- Wrap ``sys.modules`` dictionary in an "opaque" dictionary class,
  such that the representation string does not list all loaded
  modules. [malthe]

1.0b15 (2009/04/24)
-------------------

- Removed lxml extra, as we do no longer depend on it. [malthe]

- Make sure the path expression is a simple string, not
  unicode. [malthe]

- Detect path prefix properly for ViewPageTemplateFile usage in
  doctests. [sidnei]

- The ``template`` symbol is already set by the template base
  class. [malthe]

- Set Content-Type header, for backwards compatibility with
  zope.app.pagetemplate. [sidnei]

1.0b14 (2009/03/31)
-------------------

- Updated language adapter to work with 'structure' meta
  attribute. [malthe]

1.0b13 (2009/03/23)
-------------------

- When traversing on dictionaries, only exposes dictionary items
  (never attributes); this is to avoid ambiguity. [sidnei, malthe]

- Path expressions need to pass further path items in reverse order to
  traversePathElement, because that's what it expects. [sidnei]

1.0b12 (2009/03/09)
-------------------

- Insert initial variable context into dynamic scope. The presence of
  these is expected by many application. [malthe]

1.0b11 (2009/03/05)
-------------------

- If a namespace-acquired object provides ``ITraversable``, use path
  traversal. [malthe]

- Implemented TALES function namespaces. [sidnei, malthe]

- Catch ``NameError`` in exists-traverser (return false). [malthe]

- Catch ``NameError`` in exists-evaluator (return false). [malthe]

- If the supplied ``context`` and ``request`` parameters are trivial,
  get them from the view instance. [malthe]

- Expressions in text templates are never escaped. [malthe]

- Do not bind template to a trivial instance. [malthe]

1.0b10 (2009/02/24)
-------------------

- Fixed exists-traverser such that it always returns a boolean
  value. [malthe]

1.0b9 (2009/02/19)
------------------

- When evaluating path-expressions at runtime (e.g. the ``path``
  method), run the source through the transform first to support
  dynamic scope. [malthe]

1.0b8 (2009/02/17)
------------------

- Allow attribute access to ``__call__`` method on bound page
  templates. [malthe]

1.0b7 (2009/02/13)
------------------

- Fixed issue where symbol mapping would not be carried through under
  a negation (not). [malthe]

- Optimize simple case: if path expression is a single path and path
  is 'nothing' or has 'nocall:', just return value as-is, without
  going through path_traverse. [sidnei]

- Moved evaluate_path and evaluate_exists over from ``five.pt``, adds
  support for global ``path()`` and ``exists()`` functions for use in
  ``python:`` expressions (LP #317967).

- Added Zope security declaration for the repeat dictionary (tales
  iterator). [malthe]

1.0b6 (2008/12/18)
------------------

- The 'not' pragma acts recursively. [malthe]

1.0b5 (2008/12/15)
------------------

- View templates now support argument-passing for alternative context
  and request (for compatibility with
  ``zope.app.pagetemplate``). [malthe]

- Switched off the $-interpolation feature per default; It may be activated
  on a per-template basis using ``meta:interpolation='true'``. [seletz]

- Allow more flexibility in overriding the PathTranslator method. [hannosch]

- Removed the forced defaultencoding from the benchmark suite. [hannosch]

1.0b4 (2008/11/19)
------------------

- Split out content provider function call to allow modification
  through subclassing. [malthe]

- Added language negotiation. [malthe]

- Simplified template class inheritance. [malthe]

- Added support for the question-mark operator in path-expressions. [malthe]

- Updated expressions to recent API changes. [malthe]

- Added 'exists' and 'not' translators. [malthe]

  Bug fixes

- Adjusted the bigtable benchmark test to API changes. [hannosch]

1.0b3 (2008/11/12)
------------------

- Added ``PageTemplate`` and ``PageTemplateFile`` classes. [malthe]

1.0b2 (2008/11/03)
------------------

  Bug fixes

- Allow '.' character in content provider expressions.

- Allow '+' character in path-expressions.

1.0b1 (2008/10/02)
------------------

  Package changes

- Split out compiler to "Chameleon" package. [malthe]

  Backwards incompatibilities

- Moved contents of ``z3c.pt.macro`` module into
  ``z3c.pt.template``. [malthe]

- Namespace attribute "xmlns" no longer rendered for templates with no
  explicit document type. [malthe]

- Changes to template method signatures. [malthe]

- Engine now expects all strings to be unicode or contain ASCII
  characters only, unless an encoding is provided. [malthe]

- The default path traverser no longer proxies objects. [malthe]

- Template output is now always converted to unicode. [malthe]

- The ``ViewPageTemplateFile`` class now uses 'path' as the default
  expression type. [malthe]

- The compiler now expects an instantiated parser instance. [malthe]

  Features

- Added expression translator "provider:" (which renders a content
  provider as defined in the ``zope.contentprovider``
  package). [malthe]

- Added template API to render macros. [malthe]

- Optimized template loader so only a single template is instantiated
  per file. [malthe]

- Made ``z3c.pt`` a namespace package. [malthe]

- Added reduce and restore operation to the compilation and rendering
  flow in the test examples to verify integrity. [malthe]

- The ZPT parser now supports prefixed native attributes,
  e.g. <tal:foo tal:bar="" />. [malthe]

- Source-code is now written to disk in debug mode. [malthe]

- Custom validation error is now raised if inserted string does not
  validate (when debug mode is enabled). [malthe]

- Added support for omitting rendering of HTML "toggle" attributes
  (option's ``selected`` and input's ``checked``) within dynamic
  attribute assignment.  If the value of the expression in the
  assignment evaluates equal to boolean False, the attribute will not
  be rendered.  If the value of the expression in the assignment
  evaluates equal to boolean True, the attribute will be rendered and
  the value of the attribute will be the value returned by the
  expression. [chrism]

- XML namespace attribute is now always printed for root tag. [malthe]

- Allow standard HTML entities. [malthe]

- Added compiler option to specify an implicit doctype; this is
  currently used by the template classes to let the loose XHTML
  doctype be the default. [malthe]

- Added support for translation of tag body. [malthe]

- Added security configuration for the TALES iterator (repeat
  dictionary). This is made conditional on the availability of the
  application security framework. [malthe]

- Dynamic attributes are now ordered as they appear in the
  template. [malthe]

- Added ``symbol_mapping`` attribute to code streams such that
  function dependencies can be registered at compile-time. [malthe]

- Allow BaseTemplate-derived classes (PageTemplate, PageTemplateFile,
  et. al) to accept a ``doctype`` argument, which will override the
  doctype supplied by the source of the template if specified. [chrism]

- Language negotiation is left to the page template superclass, so we
  don't need to pass in a translation context anymore. [malthe]

- The ``ViewPageTemplateFile`` class now uses the module path of the
  calling class to get an absolute path to a relative filename passed
  to the constructor. [malthe]

- Added limited support for the XInclude ``include`` directive. The
  implemented subset corresponds to the Genshi implementation, except
  Match-templates, which are not made available to the calling
  template. [malthe]

- Use a global template registry for templates on the
  file-system. This makes it inexpensive to have multiple template
  class instances pointing to the same file. [malthe]

- Reimplemented the disk cache to correctly restore all template
  data. This implementation keeps a cache in a pickled format in a
  file next to the original template. [malthe]

- Refactored compilation classes to better separate concerns. [malthe]

- Genshi macros (py:def) are now available globally. [malthe]

- A syntax error is now raised when an interpolation expression is not
  exhausted, e.g. only a part of the string is a valid
  Python-expression. [malthe]

- System variables are now defined in a configuration class. [malthe]

- Improve performance of codegen by not repeatedly calling
  an expensive "flatten" function. [chrism]

- Remove ``safe_render`` implementation detail.  It hid information
  in tracebacks. [chrism]

- Implemented TAL global defines. [malthe]

- Added support for variables with global scope. [malthe]

- Curly braces may now be omitted in an expression interpolation if
  the expression is just a variable name; this complies with the
  Genshi syntax. [malthe]

- UTF-8 encode Unicode attribute literals. [chrism]

- Substantially reduced compiler overhead for lxml CDATA
  workaround. [malthe]

- Split out element compiler classes for Genshi and Zope language
  dialects. [malthe]

- Make lxml a setuptools "extra".  To install with lxml support
  (currently required by Genshi), specify "z3c.pt [lxml]" in
  any references you need to make to the package in buildout or
  in setup.py install_requires.  [chrism]

- Add test-nolxml and py-nolxml parts to buildout so the package's
  tests can be run without lxml.  [chrism]

- No longer require default namespace. [malthe]

- Changed source code debug mode files to be named <filename>.py instead of
  <filename>.source.

- Generalized ElementTree-import to allow both Python 2.5's
  ``xml.etree`` module and the standalone ``ElementTree``
  package. [malthe]

- Expression results are now validated for XML correctness when the
  compiler is running in debug-mode. [malthe]

- Preliminary support for using ``xml.etree`` as fallback for
  ``lxml.etree``. [malthe]

- String-expressions may now contain semi-colons using a double
  semi-colon literal (;;). [malthe]

- Preserve CDATA sections. [malthe]

- Get rid of package-relative magic in constructor of BaseTemplateFile
  in favor of just requiring an absolute path or a path relative
  to getcwd(). Rationale: it didn't work when called from __main__
  when the template was relative to getcwd(), which is the 99% case
  for people first trying it out. [chrism]

- Added support for METAL.
  [malthe]

- Add a TemplateLoader class to have a convenient method to instantiate
  templates. This is similar to the template loaders from other template
  toolkits and makes integration with Pylons a lot simpler.
  [wichert]

- Switch from hardcoding all options in config.py to using parameters
  for the template. This also allows us to use the more logical
  auto_reload flag instead of reusing PROD_MODE, which is also used
  for other purposes.
  [wichert]

- Treat comments, processing instructions, and named entities in the
  source template as "literals", which will be rendered into the
  output unchanged. [chrism]

  Bugfixes

- Skip elements in a "define-slot" clause if its being filled by the
  calling template. [malthe]

- Support "fill-slot" on elements with METAL namespace. [malthe]

- Omit element text when rendering macro. [malthe]

- ``Macros`` class should not return callable functions, but rather a
  ``Macro`` object, which has a ``render``-method. This makes it
  possible to use a path-expression to get to a macro without calling
  it. [malthe]

- Fixed bug where a repeat-clause would reset the repeat variable
  before evaluating the expression. [malthe]

- Fixed an issue related to correct restoring of ghosted template
  objects. [malthe]

- Implicit doctype is correctly reestablished from cache. [malthe]

- Remove namespace declaration on root tag to work around syntax error
  raised when parsing an XML tree loaded from the file cache. [malthe]

- Attribute assignments with an expression value that started with the
  characters ``in`` (e.g. ``info.somename``) would be rendered to the
  generated Python without the ``in`` prefix (as
  e.g. ``fo.somename``). [chrism]

- When filling METAL slots (possibly with a specific version of
  libxml2, I am using 2.6.32) it was possible to cause the translator
  to attempt to add a stringtype to a NoneType (on a line that reads
  ``variable = self.symbols.slot+element.node.fill_slot`` because an
  XPath expression looking for fill-slot nodes did not work
  properly). [chrism]

- Preserve whitespace in string translation expressions. [malthe]

- Fixed interpolation bug where multiple attributes with interpolation
  expressions would result in corrupted output. [malthe]

- Support try-except operator ('|') when 'python' is the default
  expression type. [malthe]

- METAL macros should render in the template where they're
  defined. [malthe]

- Avoid printing a line-break when we repeat over a single item
  only. [malthe]

- Corrected Genshi namespace (needs a trailing slash). [malthe]

- Fixed a few more UnicodeDecodeErrors (test contributed by Wiggy).
  In particular, never upcast to unicode during transformation, and
  utf-8 encode Unicode attribute keys and values in Assign expressions
  (e.g. py:attrs). [chrism]

- Fixed off-by-one bug in interpolation routine. [malthe]

- The repeat-clause should not output tail with every iteration. [malthe]

- CDATA sections are now correctly handled when using the
  ElementTree-parser. [malthe]

- Fixed bug in path-expressions where string instances would be
  (attempted) called. [malthe]

- CDATA sections are now correctly preserved when using expression
  interpolation. [malthe]

- The Genshi interpolation operator ${} should not have its result
  escaped when used in the text or tail regions. [malthe]

- Fixed edge case bug where inserting both a numeric entity and a
  literal set of unicode bytes into the same document would cause a
  UnicodeDecodeError. See also
  http://groups.google.com/group/z3c_pt/browse_thread/thread/aea963d25a1778d0?hl=en
  [chrism]

- Static attributes are now properly overriden by py:attr-attributes.
  [malthe]

0.9 (2008/08/07)
----------------

- Added support for Genshi-templates.
  [malthe]

- Cleanup and refactoring of translation module.
  [malthe]

- If the template source contains a DOCTYPE declaration, output it
  during rendering. [chrism]

- Fixed an error where numeric entities specified in text or tail
  portions of elements would cause a UnicodeDecodeError to be raised
  on systems configured with an 'ascii' default encoding. [chrism]

- Refactored file system based cache a bit and added a simple benchmark for
  the cache. The initial load speed for a template goes down significantly
  with the cache. Compared to zope.pagetemplate we are only 3x slower,
  compared to 50x slower when cooking each template on process startup.

- Got rid entirely of the _escape function and inlined the actual code
  instead. We go up again to 12x for path and 19x for Python expressions :)
  [hannosch]

- Avoid string concatenation and use multiple write statements instead. These
  are faster now, since we use a list append internally.
  [hannosch]

- Inline the _escape function, because function calls are expensive in Python.
  Added missing escaping for Unicode values.
  [fschulze, hannosch]

- When templates are instantiated outside of a class-definition, a
  relative file path will be made absolute using the module path.
  [malthe]

- Simplified the _escape function handling by pulling in the str call into the
  function. Corrected the bigtable hotshot test to only benchmark rendering.

- Replaced the cgi.escape function by an optimized local version, we go up
  to 11x for path and 16x for Python expressions :) In the bigtable benchmark
  the enhancement is more noticable - we are the same speed as spitfire -O1
  templates now and just half the speed of -O3 :))

- Added a new benchmark test called bigtable that produces results which are
  directly comparable to those produced by the bigtable.py benchmark in the
  spitfire project.

- Introduce a new config option called `Z3C_PT_DISABLE_I18N`. If this
  environment variable is set to `true`, the template engine will not call
  into the zope.i18n machinery anymore, but fall back to simple interpolation
  in all cases. In a normal Zope environment that has the whole i18n
  infrastructure set up, this will render the templates about 15x faster than
  normal TAL, instead of only 10x faster at this point.

- Removed the `second rendering` tests from the benchmark suite. Since we
  enable the file cache for the benchmarks, there's no difference between the
  first and second rendering anymore after the cache file has been written.

- Require zope.i18n 3.5 and add support for using its new negotiate function.
  If you use the `zope_i18n_allowed_languages` environment variable the target
  language for a template is only negotiated once per template, instead of
  once for each translate function call. This more than doubles the speed
  and the benchmark is back at 9.2 times faster.

- Extended the i18n handling to respect the passed in translation context to
  the template. Usually this is the request, which is passed on under the
  internal name of `_context` into the render functions. After extending the
  i18n tests to include a negotiator and message catalog the improvement is
  only at 4.5 anymore, as most of the time is spent inside the i18n machinery.

- Added persistent file cache functionality. If the environment variable is
  set, each file system based template will add a directory to the cache
  (currently a SHA-1 of the file's absolute path is used as the folder name)
  and in the folder one file per params for the template (cache filename is
  the hash of the params). Once a template file is initialized, an instance
  local registry is added, which then looks up all cached files and
  pre-populates the registry with the render functions.

- Fixed interpolation edge case bugs.
  [malthe]

- Added new `Z3C_PT_FILECACHE` environment variable pointing to a directory.
  If set, this will be used to cache the compiled files.

- Added a second variation of the repeat clause, using a simple for loop. It
  doesn't support the repeatdict, though and is therefor not used yet. Also
  began work to add introspection facilities to clauses about the variables
  being used in them. The simpler loop causes the benchmarks to go up to a
  10.5 (old 9.5) for path expressions and 14.5 (12.5) for python expressions.
  So the next step is to introduce an optimization phase, that can decide
  which variant of the loops to use.

- Made the debug mode independent from the Python debug mode. You can now
  specify an environment variable called `Z3C_PT_DEBUG` to enable it.

- Added some code in a filecache module that can later be used to write out
  and reload the compiled Python code to and from the file system. We should
  be able to avoid reparsing on Python process restart.

- Simplified the generated _escape code. cgi.escape's second argument is a
  simple boolean and not a list of characters to quote.

- Use a simple list based BufferIO class instead of a cStringIO for the out
  stream. Avoiding the need to encode Unicode data is a bigger win. We do
  not support arbitrarily mixing of Unicode and non-ascii inside the engine.

- Merged two adjacent writes into one inside the Tag clause.

- Applied a bunch of micro-optimizations. ''.join({}) is slightly faster
  than ''.join({}.keys()) and does the same. Avoid a try/except for error
  handling in non-debug mode. Test against 'is None' instead of a boolean
  check for the result of the template registry lookup. Made PROD_MODE
  available defined as 'not DEBUG_MODE' in config.py, so we avoid the 'not'
  in every cook-check.

- Added more benchmark tests for the file variants.

- Optimized 'is None' handling in Tag clause similar to the Write clause.

- Made the _out.write method directly available as _write in all scopes, so
  we avoid the method lookup call each time.

- Optimized 'is None' handling in Write clause.

- Slightly refactored benchmark tests and added tests for the file variants.

- In debug mode the actual source code for file templates is written out to
  a <filename>.source file, to make it easier to inspect it.

- Make debug mode setting explicit in a config.py. Currently it is bound to
  Python's __debug__, which is False when run with -O and otherwise True.

- Use a simplified UnicodeWrite clause for the result of _translate calls,
  as the result value is guaranteed to be Unicode.

- Added benchmark tests for i18n handling.

- Added more tests for i18n attributes handling.

- Don't generate empty mappings for expressions with a trailing semicolon.

- Fixed undefined name 'static' error in i18n attributes handling and added
  quoting to i18n attributes.

- Added condition to the valid attributes on tags in the tal namespace.

- Made sure the traceback from the *first* template exception
  is carried over to __traceback_info__

- Added template source annotations on exceptions raised while
  rendering a template.

0.8 (2008/03/19)
----------------

- Added support for 'nocall' and 'not' (for path-expressions).

- Added support for path- and string-expressions.

- Abstracted expression translation engine. Expression implementations
  are now pluggable. Expression name pragmas are supported throughout.

- Formalized expression types

- Added support for 'structure'-keyword for replace and content.

- Result of 'replace' and 'content' is now escaped by default.

- Benchmark is now built as a custom testrunner

0.7 (2008/03/10)
----------------

- Added support for comments; expressions are allowed
  inside comments, i.e.

     <!-- ${'Hello World!'} -->

  Comments are always included.

0.7 (2008/02/24)
----------------

- Added support for text templates; these allow expression
  interpolation in non-XML documents like CSS stylesheets and
  javascript files.

0.5 (2008/02/23)
----------------

- Expression interpolation implemented.

0.4 (2008/02/22)
----------------

- Engine now uses cStringIO yielding a 2.5x performance
  improvement. Unicode is now handled correctly.

0.3 (2007/12/23)
----------------

- Code optimization; bug fixing spree

- Added ``ViewPageTemplateFile`` class

- Added support for i18n

- Engine rewrite; improved code generation abstractions

0.2 (2007/12/05)
----------------

- Major optimizations to the generated code

0.1 (2007/12/03)
----------------

- First public release
